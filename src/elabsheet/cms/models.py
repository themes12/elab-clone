import re
import os
import inspect
from django.db import models
from django.db.utils import IntegrityError
from django.template import Context,Template
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.dispatch import receiver

from .markdown_processor import process_markdown_source,insert_test_dialog
from .elab import Code
from sandbox import Sandbox,SourceCode
from .fields import CodeField
from commons.fields import LongJSONField
from commons.models import TestCaseResult

LANGS = ((x,x) for x in Sandbox.get_languages())

RE_REMOVE_WS = re.compile(r'\s')


class TagManager(models.Manager):
    """
    TagManager adds support for filter_by_tags to a model with tags.
    However, this method must be called directly from Model.objects,
    e.g., Model.objects.filter(xxx).filter_by_tags('hello') won't
    work.
    """

    # Tags routines
    @staticmethod
    def normalize_space(st):
        return ' '.join(st.strip().split())

    @staticmethod
    def normalize_tags(tags):
        """
        Returns a list of tags, space-normalized.
        """
        return [TagManager.normalize_space(x) for x in tags.split(',')]
   
    def filter_by_tags(self,tags):
        taglist = TagManager.normalize_tags(tags)
        candidates = self.model.objects.all()
        for tag in taglist:
            candidates = candidates.filter(tags__contains=tag)
        return candidates

class InvalidGenerator(Exception):
    pass

class InvalidTextGrader(Exception):
    pass

class Task(models.Model):
    """
    Task is a central model for E-Labsheet.

    It stores the basic unit of any labsheet: a task which consists of
    description, solution, code with fill-in form, and testdata (a set
    of testcases).
    
    It is also resposible for grading students' answers (mainly by
    executing the filled-in solution in a Sandbox and compare
    solutions).

    """
    name = models.CharField(max_length=100)
    note = models.CharField(max_length=100,
                            blank=True,
                            default='',
                            help_text='A one-line summary '
                            'of the task to be shown when '
                            'lab designer selects tasks.')
    source = models.TextField()
    language = models.CharField(max_length=20,choices=LANGS)
    lang_options = models.TextField(blank=True)
    html_template = models.TextField(blank=True)
    code = CodeField(blank=True)

    creator = models.ForeignKey(User,related_name='tasks_created',
                                blank=True,null=True,
                                on_delete=models.SET_NULL)
    owner = models.ForeignKey(User,related_name='tasks_owned',
                              blank=True,null=True,
                              on_delete=models.SET_NULL)

    disabled = models.BooleanField(blank=True,default=False)
    version = models.IntegerField(default=1)
    previous_version = models.ForeignKey('self',blank=True,
                                         null=True,default=None,
                                         on_delete=models.SET_NULL)

    is_private = models.BooleanField(default=False,
                help_text='If checked, this task becomes private to its creator '
                          'and owner')
    
    # simplest way to implement tags
    tags = models.CharField(max_length=200,
                            blank=True,
                            default='',
                            help_text='A comma-separated list '
                            'of tags. Each tag may contain spaces.')

    generator = models.TextField(
            blank=True,
            null=True,
            help_text=
                'Python script defining the function'
                ' <tt>generate(seed,difficulty)</tt> to generate a child task'
                ' by returning a dict of variable substituions.'
            )

    text_grader = models.TextField(
            blank=True,
            null=True,
            help_text=
                'Python script defining the function'
                ' <tt>grade(index,max_score,solution,answer)</tt> or'
                ' <tt>grade(index,max_score,solution,answer,elab)</tt>' 
                ' to return a score for the given answer,'
                ' or None if the answer is not to be graded.'
            )

    testcases = LongJSONField(blank=True, null=True)
    textblanks = LongJSONField(blank=True, null=True)

    objects = TagManager()

    def __str__(self):
        if (not self.disabled) or ('disabled' in self.name):
            return self.name
        else:
            return self.name + ' (disabled)'

    def enabled(self):
        return not self.disabled
    enabled.boolean = True   # This is needed for the admin page.
    
    ###########################
    # Various accessors
    #

    def solution(self):
        """
        Return the solution code from source.
        """
        return self.code.dump_solution()

    @staticmethod
    def build_blank_html_from_template(html_template):
        try:
            template = Template(html_template)
            context = Context({})
            return template.render(context)
        except Exception as e:
            #import traceback
            #traceback.print_exc()
            return "<p style='color:red'>Rendering error: {}<br/>{}</p>".format(
                    e.__class__.__name__,
                    e.template_debug["message"],
                    )

    @staticmethod
    def build_html_from_source(source,language):
        html,code,tests,textblanks = process_markdown_source(source,language)
        return Task.build_blank_html_from_template(html),textblanks

    def html(self):
        """
        Return a rendered html (with rendered forms) to be displayed.
        """
        return Task.build_blank_html_from_template(self.html_template)

    def has_manual_grading(self):
        return len(self.textblanks) != 0

    def manual_full_score(self):
        return sum([blank['score'] for blank in self.textblanks])

    ###########################
    # Methods for grading
    #

    @staticmethod
    def compare_result(result,expected):
        """
        Compare outputs from students' submission with the output from
        the provided solution.

        Currently all trailing whitespaces are removed before comparison.
        """
        if result is None:
            return TestCaseResult.FAILED
        result = '\n'.join([line.rstrip() for line in result.split('\n')])
        expected = '\n'.join([line.rstrip() for line in expected.split('\n')])
        if result.rstrip() == expected.rstrip():
            return TestCaseResult.PASSED
        if result.rstrip().lower() == expected.rstrip().lower():
            return TestCaseResult.CASEPROBLEM
        if RE_REMOVE_WS.sub('',result) == RE_REMOVE_WS.sub('',expected):
            return TestCaseResult.SPACEPROBLEM
        return TestCaseResult.FAILED


    def evaluate_built_source_with_messages(self,built_source,sandbox,
                                            input_data,
                                            capture=False):

        for supplement in self.supplement_set.all():
            supplement.unzip_to(sandbox.get_scratch_dir())

        output = sandbox.evaluate(built_source=built_source,
                                  input_string=input_data,
                                  capture=capture)

        messages = sandbox.get_compiler_messages()

        return output,messages


    def verify_with_messages(self,answer,output_list=None):
        submitted_code = self.code.dump(answer)
        src = SourceCode(self.language ,submitted_code)
        results = []
        messages = ''

        sandbox = Sandbox(settings.SANDBOX_SCRATCH_DIR,
                          temp_subdir=True,clean_dir=False,flags=self.code.flags)
        # extract supplements into scratch dir for compiling
        for supplement in self.supplement_set.all():
            supplement.unzip_to(sandbox.get_scratch_dir())
        built_source = sandbox.build(src)

        for testcase in self.testcases:
            output,messages = (
                self.evaluate_built_source_with_messages(
                    built_source,
                    sandbox,
                    testcase['input']+'\n')
                )

            this_result = {'task' : self,
                           'testcase' : testcase}
            this_result['passed'] = Task.compare_result(output,testcase['output'])
            results.append(this_result)
            if output_list!=None:
                output_list.append(output)

        sandbox.clean_scratch_dir()
        return results,messages


    def verify(self,answer,output_list=None):
        results,messages = self.verify_with_messages(answer,output_list)
        return results


    def verify_manual_auto_gradable_fields(self,answer):
        manual_scores = {}

        compiled_grader = self.compile_text_grader()
        # create dict for blank/answer pairs (answer key starts from zero)
        all_blanks = {}
        for b in self.textblanks:
            id = int(b['id'])
            if id-1 in answer:
                all_blanks[id] = (TextBlank(b,compiled_grader),answer[id-1])
            else:
                all_blanks[id] = (TextBlank(b,compiled_grader),None)
        for blank,ans in all_blanks.values():
            if not blank.auto_gradable:
                continue
            if ans is None:
                manual_scores[f'b{blank.id}'] = 0
                continue
            manual_scores[f'b{blank.id}'] = blank.grade_answer(ans,all_blanks)
        if manual_scores != {}:
            return manual_scores
        else:
            return None

    ###########################
    # Saving preparation methods
    #

    def run_testcase(self,built_source,sandbox,
                      input_data,capture=False):
        output,messages = self.evaluate_built_source_with_messages(
            built_source,sandbox,
            input_data+'\n',
            capture)

        return output

    def run_testcases(self):
        solution = self.code.dump_solution()
        src = SourceCode(self.language,solution)
        sandbox = Sandbox(settings.SANDBOX_SCRATCH_DIR,
                          temp_subdir=True,clean_dir=False,flags=self.code.flags)
        # extract supplements into scratch dir for compiling
        for supplement in self.supplement_set.all():
            supplement.unzip_to(sandbox.get_scratch_dir())
        built_source = sandbox.build(src)

        for test in self.testcases:
            test['output'] = self.run_testcase(built_source,sandbox,test['input'])
   
    def build_from_source(self,run_testcases=True):
        """
        Generate and populate the model with html template, solution code,
        test cases, and text-based answers from Markdown source.
        """
        html,code,tests,blanks = process_markdown_source(self.source,self.language)
        self.html_template = html
        self.code = code

        textblanks = []
        for (id,(sol,score)) in blanks.items():
            textblanks.append({
                'id' : id,
                'solution' : sol,
                'score' : score,
                })
        self.textblanks = textblanks

        testcases = []
        for test in tests:
            testcases.append({
                'input' : test.input,
                'output' : None,
                'visible' : test.visible,
                'hint' : test.hint,
                })
        self.testcases = testcases

        if run_testcases:
            self.run_testcases()

    def preprocess_tags(self):
        self.tags = ', '.join(TagManager.normalize_tags(self.tags))

    def is_supertask(self):
        return self.generator is not None and self.generator.strip() != ''
    is_supertask.short_description = "SuperTask"
    is_supertask.boolean = True

    def is_childtask(self):
        return self.__class__ == ChildTask

    def is_concrete(self):
        return (not self.is_supertask()) or \
               (self.is_supertask() and self.is_childtask())

    def make_concrete(self,seed,difficulty):
        """
        If the current task is a super task, transform it into a child task
        with the provided parameters.  This does nothing for regular task.
        """
        if self.is_supertask():
            ChildTask.transform(self,seed,difficulty)

    def clean(self):
        # try compiling child task generator, if provided
        try:
            self.compile_generator()
        except InvalidGenerator as e:
            raise ValidationError({'generator':str(e)})

        # try compiling text grader, if provided
        try:
            self.compile_text_grader()
        except InvalidTextGrader as e:
            raise ValidationError({'text_grader':str(e)})

    def save(self,force_insert=False,force_update=False):
        # pre-render html template, code, testcases, textblanks, and tags
        # before saving
        if self.is_supertask():
            self.build_from_source(run_testcases=False)
        else:
            self.build_from_source(run_testcases=True)
        self.preprocess_tags()
        super(Task,self).save(force_insert,force_update)

        # delete all associated cached child tasks
        CachedChildTask.objects.filter(parent_task=self).delete()

    def compile_generator(self):
        if not self.generator:
            return None
        try:
            compiled = compile(self.generator,'<generator>',mode='exec')
            gvars = {}
            exec(compiled,gvars)
        except Exception as e:
            raise InvalidGenerator(str(e))

        # make sure generate(seed,difficulty) is defined
        if 'generate' not in gvars:
            raise InvalidGenerator("Function 'generate' not defined")
        generate_func = gvars['generate']
        if not callable(generate_func):
            raise InvalidGenerator("Object 'generate' is not a function")
        sig = inspect.signature(generate_func)
        if list(sig.parameters.keys()) != ['seed','difficulty']:
            raise InvalidGenerator(
                    "Incorrect signature for generate(seed,difficulty) function")

        # optionally, adjust_parameters(seed,difficulty) may also be defined
        adjust_parameters_func = None
        if 'adjust_parameters' in gvars:
            adjust_parameters_func = gvars['adjust_parameters']
            if not callable(adjust_parameters_func):
                raise InvalidGenerator("Object 'adjust_parameters' is not a function")
            sig = inspect.signature(adjust_parameters_func)
            if list(sig.parameters.keys()) != ['seed','difficulty']:
                raise InvalidGenerator(
                        "Incorrect signature for adjust_parameters(seed,difficulty) function")
        return generate_func, adjust_parameters_func

    def compile_text_grader(self):
        if not self.text_grader:
            return None
        try:
            compiled = compile(self.text_grader,'<text-grader>',mode='exec')
            gvars = {}
            exec(compiled,gvars)
        except Exception as e:
            raise InvalidTextGrader(str(e))
        if 'grade' not in gvars:
            raise InvalidTextGrader("Function 'grade' not defined")
        grade_func = gvars['grade']
        if not callable(grade_func):
            raise InvalidTextGrader("Object 'grade' is not a function")
        sig = inspect.signature(grade_func)
        if list(sig.parameters.keys()) == \
               ['index','max_score','solution','answer']:
            grade_func.with_elab = False
        elif list(sig.parameters.keys()) == \
               ['index','max_score','solution','answer', 'elab']:
            grade_func.with_elab = True
        else:
            raise InvalidTextGrader("Incorrect signature for grade() function")
        return grade_func

    @staticmethod
    def search_by_tags(tags):
        return Task.objects.filter_by_tags(tags).filter(disabled=False)


class Lab(models.Model):
    name = models.CharField(max_length=100)
    tags = models.CharField(max_length=200,
                            blank=True,
                            default='',
                            help_text='A comma-separated list '
                            'of tags. Each tag may contain spaces.')
    disabled = models.BooleanField(blank=True,default=False)

    objects = TagManager()

    def __str__(self):
        return self.name

    def preprocess_tags(self):
        self.tags = ', '.join(TagManager.normalize_tags(self.tags))

    def save(self,force_insert=False,force_update=False):
        self.preprocess_tags()
        super(Lab,self).save(force_insert,force_update)

    @staticmethod
    def search_by_tags(tags):
        return Lab.objects.filter_by_tags(tags).filter(disabled=False)
   

class Assignment(models.Model):
    """
    Assignment joins Lab and Task.  It also provide additional
    numbering of tasks in each lab.  Currently this numbering is sorted
    as string; therefore, to get task number 1.2 before task number
    1.10, you have to write 1.02 and 1.10.
    """
    task = models.ForeignKey(Task,on_delete=models.CASCADE)
    lab = models.ForeignKey(Lab,blank=True,null=True,on_delete=models.CASCADE)
    number = models.CharField(max_length=20)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return "%s %s" % (self.number,self.task.name)

    def html(self):
        if self.task:
            return self.task.html()
        else:
            return None

    def get_recent_submission_for_user(self,user,section):
        try:
            submission = (user.submission_set
                    .filter(assignment=self,section=section)
                    .reverse()[0])
            submission.make_task_concrete()
            return submission
        except:
            return None

    def get_submissions_for_user(self,user,section):
        try:
            submissions = (user.submission_set
                    .select_related()
                    .filter(assignment=self,section=section)
                    .reverse())
            for s in submissions:
                s.make_task_concrete()
            return submissions
        except:
            return None

    @staticmethod
    def next_number(num):
        """
        Returns next number.  used to generate fill-in for admin form
        for adding task to lab.
        
        >>> Assignment.next_number('0')
        '1'
        >>> Assignment.next_number('1')
        '2'
        >>> Assignment.next_number('9')
        '10'
        >>> Assignment.next_number('1.5')
        '2.0'
        >>> Assignment.next_number('1.50')
        '2.00'
        >>> Assignment.next_number('01.50')
        '02.00'

        """
        nums = num.split('.')
        first = nums[0]
        if first=='':
            return '0'
        else:
            try:
                nfirst = str(int(first)+1)
                newfirst = '0'*(len(first)-len(nfirst)) + nfirst
            except:
                newfirst = '0'
            newnums = ['0'*(len(item)) for item in nums]
            newnums[0] = newfirst
            return '.'.join(newnums)

    def make_task_concrete_for_user(self,user,section):
        if self.lab:
            lab_id = self.lab_id 
        else:
            lab_id = 0
        self.task.make_concrete(user.id+section.id+lab_id,0)

    def submission_count(self):
        return self.submission_set.count()
    submission_count.short_description = "Submission Count"


class Course(models.Model):
    """
    A Course groups a set of labs together.  

    A single real course, e.g., 204111 Computer and Programming, can
    have many Courses; each has a different set of course materials.
    These Courses then share the same number and name, but with
    different notes.
    
    """
    number = models.CharField(max_length=10)
    name = models.CharField(max_length=100,
                            help_text='The name of the course according '
                            'to the course number.  Other information '
                            'should be put in "note."')
    authors = models.ManyToManyField(User,
                                     help_text='A list of users that '
                                     'can edit this course materials.')
    note = models.CharField(max_length=100,
                            blank=True,
                            help_text='A one-line short note identifying '
                            'this particular set of course material. '
                            'Can be blank, if it\'s unique.')
    comments = models.TextField(blank=True,
                                help_text='More detailed explanation for '
                                '"note."')
    labs = models.ManyToManyField(Lab,through='LabInCourse')

    def __str__(self):
        if self.note:
            return "%s %s (%s)" % (self.number,self.name,self.note)
        else:
            return "%s %s" % (self.number,self.name)


class LabInCourse(models.Model):
    """
    LabInCourse joins Course and Lab, adding a property number for
    sorting.  This is resemble the Assignment model.
    
    TODO: Better name for this join model.
    """
    lab = models.ForeignKey(Lab,on_delete=models.CASCADE)
    course = models.ForeignKey(Course,on_delete=models.CASCADE)
    number = models.CharField(max_length=20)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return "%s %s" % (self.number,self.lab)


class ElabTextGrader:
    """
    Utility class to be used by text grader
    """
    def __init__(self,all_blanks):
        self.blanks = {id:all_blanks[id][0] for id in all_blanks}
        self.answers = {id:all_blanks[id][1] for id in all_blanks}

    def grade(self,id):
        try:
            blank = self.blanks[id]
            answer = self.answers[id]
            return blank.grade_answer(answer,self.blanks)
        except:
            return 0


class TextBlank:
    """
    Wrapper class to store information about a text-based question, which includes blank ID,
    solution and score.
    """
    def __init__(self,textblank_from_task,grader):
        self.id = textblank_from_task['id']
        self.grader = grader
        sol = textblank_from_task['solution']
        self.auto_gradable = (len(sol) > 0 and sol[0]=='!' and sol[-1]=='!')
        if self.auto_gradable:
            self.solution = sol[1:-1]
        else:
            self.solution = sol
        self.score = textblank_from_task['score']

    def grade_answer(self,answer,all_blanks):
        # try exact match first
        if self.solution.strip() == answer.strip():
            return self.score
        # try grader if available
        elif self.grader is not None:
            elab = ElabTextGrader(all_blanks)
            try:
                if self.grader.with_elab:
                    score = self.grader(self.id,
                                        self.score,
                                        self.solution,
                                        answer,
                                        elab)
                else:
                    score = self.grader(self.id,
                                        self.score,
                                        self.solution,
                                        answer)
            except Exception as e:
                #print(str(e))
                score = 0
            if type(score) != int:
                return 0
            # make sure 0 <= score <= max_score
            return max(min(score,self.score),0)
        # give zero score, otherwise
        else:
            return 0

    def __repr__(self):
        return f'[{self.score},{self.auto_gradable}] {self.solution}'

    def solution_for_js(self):
        '''Generates escaped string from solution to be used in Javascript
        string.'''
        return self.solution \
                .replace('\\','\\\\') \
                .replace("'","\\'")  \
                .replace('"','\\"')   \
                .replace('\n','<cr>')


class GradingSupplement(models.Model):
    """
    Stores supplemental files to be unzipped and copied to sandbox
    when evaluating submissions.  Currently, the original filename is
    not stored; thus, to prevent uncontrolable input filename changes,
    the file should be compressed (so that filenames inside the zipped
    file are preserved).
    """
    task = models.ForeignKey(Task,related_name='supplement_set',on_delete=models.CASCADE)
    data_file = models.FileField(upload_to='supplements/%Y/%m/%d')

    def unzip_to(self,path):
        filename = self.data_file.path

        if filename.endswith('zip'):

            import zipfile
            import os.path
            import os

            zf = zipfile.ZipFile(filename)
            zf.extractall(path)

        elif (filename.endswith('tar') or 
              filename.endswith('tgz') or
              filename.endswith('tar.gz')):

            import tarfile

            tf = tarfile.open(filename)
            tf.extractall(path)

    def clone(self):
        import os.path
        new_supplement = GradingSupplement(task=self.task)
        contents = ContentFile(self.data_file.read())
        orig_filename = os.path.split(self.data_file.name)[-1]
        new_supplement.data_file.save(orig_filename,contents)
        self.data_file.close()
        new_supplement.save()
        return new_supplement

        # TODO: make a unit test
        #
        # for debugging
        # import os
        # print 'Extract supplement to ', path
        # for entry in os.listdir(path):
        #     print entry
        # print '----'

@receiver(models.signals.post_delete, sender=GradingSupplement)
def auto_delete_supplement(sender,instance,**kwargs):
    """
    Delete orphan supplement file when its GradingSupplement instance is
    deleted
    """
    if instance.data_file:
        instance.data_file.delete(save=False)


class ChildTaskException(Exception):
    pass

class ChildTask(Task):
    """
    ChildTask is a task that gets generated from a super task using the
    provided random seed and difficulty level.
    """

    class Meta:
        proxy = True

    @staticmethod
    def generate_key(seed,difficulty):
        return '{}:{}'.format(seed,difficulty)

    @staticmethod
    def decode_key(key):
        try:
            seed,difficulty = key.split(':')
            return int(seed),int(difficulty)
        except:
            return None

    @staticmethod
    def transform(supertask,seed,difficulty):
        '''
        Transform given super-task into an in-memory child task for displaying.
        Note that test case results are not yet computed now and will be
        produced during grading.
        '''
        # make sure the given task really is a super-task
        if supertask.is_supertask():
            childtask = supertask
            childtask.__class__ = ChildTask

            # there should be no error by now, as it was checked during save
            generate_func, adjust_func = childtask.compile_generator()

            # adjust the seed and difficulty values if the adjusting function is
            # provided
            generator_error = False
            if adjust_func is not None:
                try:
                    seed,difficulty = adjust_func(seed,difficulty)
                except Exception as e:
                    childtask.html_template = \
                        f'<tt style="color:red">Error in adjust_parameters(): {str(e)}</tt>'
                    generator_error = True
            childtask.seed = seed
            childtask.difficulty = difficulty
        else:
            raise Exception('This task lacks a generator.')

        key = ChildTask.generate_key(seed,difficulty)
        # check child task cache
        try:
            cache = CachedChildTask.objects.get(parent_task=supertask,key=key)
            cache.populate_childtask(childtask)
        except CachedChildTask.DoesNotExist:
            # evaluate template variables in markdown source using the generator
            # script
            try:
                substitutes = generate_func(seed,difficulty)
                if not isinstance(substitutes,dict):
                    raise Exception("The generator function does not return a dict")
            except Exception as e:
                childtask.html_template = \
                    f'<tt style="color:red">Error in generate(): {str(e)}</tt>'
                childtask.testcases = []
                childtask.textblanks = []
                generator_error = True

            if not generator_error:
                for var in substitutes.keys():
                    if not var.startswith('__'): # ignore variables like __builtins__, etc
                        childtask.source = childtask.source.replace(
                                f"@{var}@",str(substitutes[var]))
                childtask.build_from_source(run_testcases=False)

            childtask.testcases_evaluated = False
            cache = CachedChildTask(
                        parent_task=supertask,
                        key=key,
                        source=childtask.source,
                        html_template=childtask.html_template,
                        code=childtask.code,
                        testcases=childtask.testcases,
                        textblanks=childtask.textblanks,
                        testcases_evaluated=childtask.testcases_evaluated,
                    )
            # it is possible that a cached child task of the same parent and
            # key came into existence during this time, so make sure that an
            # integrity error is caught
            try:
                cache.save()
                childtask.cache = cache
            except IntegrityError:
                cache = CachedChildTask.objects.get(parent_task=supertask,key=key)
                cache.populate_childtask(childtask)

    def save(self,force_insert=False,force_update=False):
        raise ChildTaskException('ChildTask must not be saved')

    def run_testcases(self):
        super().run_testcases()
        self.cache.testcases = self.testcases
        self.cache.testcases_evaluated = True
        self.cache.save()

    def verify_with_messages(self,answer,output_list=None):
        # generate testcases' results before verifying the answer
        self.run_testcases()
        return super().verify_with_messages(answer,output_list)


class CachedChildTask(models.Model):
    """
    Store cached version of ChildTask to reduce server workload.

    """
    parent_task = models.ForeignKey(Task,on_delete=models.CASCADE)
    key = models.CharField(max_length=50)
    source = models.TextField()
    html_template = models.TextField(blank=True)
    code = CodeField(blank=True)
    testcases = LongJSONField(blank=True, null=True)
    textblanks = LongJSONField(blank=True, null=True)
    testcases_evaluated = models.BooleanField(default=False)

    class Meta:
        index_together = [
            ["parent_task","key"],
        ]
        unique_together = [
            ["parent_task","key"],
        ]

    def __str__(self):
        return '{} | {}'.format(self.parent_task, self.key)

    def evaluate_testcases(self):
        task = self.parent_task
        seed,diff = ChildTask.decode_key(self.key)
        ChildTask.transform(task,seed,diff)
        task.run_testcases()

    def populate_childtask(self,childtask):
        childtask.source = self.source
        childtask.html_template = self.html_template
        childtask.code = self.code
        childtask.testcases = self.testcases
        childtask.textblanks = self.textblanks
        childtask.testcases_evaluated = self.testcases_evaluated
        childtask.cache = self
