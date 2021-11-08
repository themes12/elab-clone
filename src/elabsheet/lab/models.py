import random
import pickle
import ipaddress

from django.db import models
from django.template import Context, Template
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils import timezone

from .fields import AnswerField, GradingResultField
from cms.models import Assignment, Task, Course, Lab
from commons.fields import JSONField
from commons.utils import \
        parse_address_list, \
        address_in_list, \
        get_remote_addr_from_request
        

class Semester(models.Model):
    """
    Only system admin can create a 'semester'.  This is used to group
    many courses together.  We need a model for this because semesters
    can be active or inactive (e.g., not shown in usual menu).
    """

    # TODO: A semester is determined by a year and a term.  I'm not
    # sure if this is the correct terminology.  Should straight this
    # out.
    year = models.IntegerField(help_text='Academic year in B.E.')
    term = models.IntegerField(choices=[(0,'summer'),
                                        (1,'first'),
                                        (2,'second')])
    start_date = models.DateField()

    def __str__(self):
        if self.term==0:
            return "%d/s" % self.year
        else:
            return "%d/%s" % (self.year, self.term)

    class Meta:
        ordering = ['-start_date']


class Section(models.Model):
    """
    represents a section for a course in a certain semester.  It keeps track
    of students currently enrolled in the section.

    In addition, it stores a section name which will typically be used to
    store the section number, and a notes field to store miscellaneous
    information.
    """
    course = models.ForeignKey(Course,on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester,on_delete=models.CASCADE)
    name = models.CharField(
               max_length=50,
               help_text='Section name or number(s)')
    notes = models.TextField(
               blank=True,
               help_text='Additional section information')
    instructors = models.ManyToManyField(
                  User,
                  blank=True,
                  related_name='instructor_set',
                  help_text='Instructor(s) and TA(s) for the section')
    students = models.ManyToManyField(
                  User,
                  blank=True,
                  related_name='student_set',
                  help_text='Students enrolled to the section')
    labs = models.ManyToManyField(Lab, through='LabInSection')
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['semester']

    def get_available_labs_in_course(self):
        course = self.course
        labs_insection = self.labinsection_set.all()
        avail_labs_incourse = []
        for lab_incourse in course.labincourse_set.all():
            found = False
            for lab_insection in labs_insection:
                if lab_incourse.lab.id == lab_insection.lab.id:
                    found = True
                    break
            if not found:
                avail_labs_incourse.append(lab_incourse)
        return avail_labs_incourse

    def has_instructor(self, user):
        return self.instructors.filter(pk=user.id).count()!=0

    def has_student(self, user):
        return self.students.filter(pk=user.id).count()!=0

    def __str__(self):
        return u"%s [%s] Sec:%s" % (self.course, self.semester, self.name)

    def published_announcements(self):
        announcements = self.announcement_set.all()
        published = []
        for ann in announcements:
            if ann.is_published:
                published.append(ann)
        return published


    def get_recent_submissions_for_assignment(self, assignment):
        """
        gets all submissions for this assignment for all students in
        this section.
        """
        latest_submission_id_for_users = (Submission.objects
                .filter(section=self,assignment=assignment)
                # Must disable sorting to prevent 'submitted_at' field
                # from being included in GROUP BY
                .order_by()
                .values("user")
                .annotate(latest_id=models.Max("id"))
                )
        submission_ids = [e['latest_id'] for e in latest_submission_id_for_users]
        submissions = Submission.objects.select_related().filter(id__in=submission_ids)
        submissions = list(submissions)
        for s in submissions:
            s.make_task_concrete()
        return submissions


    def get_recent_submissions_by_students_for_lab(self, lab):
        """
        gets all submissions for this lab for each student in this
        section.  

        returns a list of tuple (student, [recent submission for each assignment in lab])
        """
        students = self.students.all()
        std_submissions = {}
        for student in students:
            std_submissions[student.id] = {'student': student,
                                           'submissions': []}
                                           
        for assignment in lab.assignment_set.all():
            submissions = self.get_recent_submissions_for_assignment(assignment)
            appended = {}
            for submission in submissions:
                if submission.user_id not in std_submissions:
                    # if some student is not in section anymore
                    continue
                std_submissions[submission.user_id]['submissions'].append(submission)
                appended[submission.user_id] = True

            # have to append None for students who did not submit
            for user_id in std_submissions.keys():
                if user_id not in appended:
                    std_submissions[user_id]['submissions'].append(None)
        return [(std_submissions[user_id]['student'],
                 std_submissions[user_id]['submissions']) 
                for user_id in std_submissions.keys()]


class Announcement(models.Model):
    """
    is for making announcement for each section.  Each annoucement has
    a title, a body text (rendered with markdown), is_published,
    created_at, and a reference to the section.
    """
    section = models.ForeignKey(Section,on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class LabInSection(models.Model):
    """
    joins Section and Lab, adding a property number for
    sorting.
    """
    lab = models.ForeignKey(Lab,related_name='sections',on_delete=models.CASCADE)
    section = models.ForeignKey(Section,on_delete=models.CASCADE)
    number = models.CharField(max_length=20)
    disabled = models.BooleanField(blank=True, default=False)
    read_only = models.BooleanField(default=False)
    hidden_tasks = models.CharField(max_length=200,
                                    blank=True,
                                    default='',
                                    help_text='A comma-separated list of '
                                    'assignment IDs to be hidden in the lab')

    def __str__(self):
        return "%s %s" % (self.number, self.lab)

    class Meta:
        ordering = ['number']

    def passes_address_acl(self, request):
        """
        Check whether the user's request passes the address ACL, if policy is
        currently in effect
        """
        try:
            acl = self.addressacl
            if not acl.activated:
                return True
            remote_ip = get_remote_addr_from_request(request)
            if remote_ip is None:
                return False
            remote_ip_n = int(ipaddress.IPv4Address(remote_ip))
            allowed_list = acl.get_allowed_list()
            denied_list = acl.get_denied_list()
            allowed = address_in_list(remote_ip_n,allowed_list)
            denied = address_in_list(remote_ip_n,denied_list)

            # use default action if ambiguous
            if allowed == denied:
                permit = (acl.default_action == 'a')
            else: # otherwise, return whether this address is allowed
                permit = allowed

            if not permit:
                return False

            # check single-IP policy, if currently enabled
            if acl.single_ip:
                try:
                    lock = SingleIpLock.objects.get(user=request.user,labinsec=self)
                    if lock.ip != remote_ip:
                        permit = False
                    else:
                        lock.last_access = timezone.now()
                        lock.save()
                except SingleIpLock.DoesNotExist:
                    lock = SingleIpLock(
                            user=request.user,
                            labinsec=self,
                            ip=remote_ip,
                            last_access=timezone.now())
                    lock.save()
                    permit = True

            return permit

        except AddressAcl.DoesNotExist:
            # no ACL defined for this lab; simply allow access
            return True

    @staticmethod
    def get_direct_to_lab(request):
        try:
            session_labinsec_id = request.session['DIRECT-TO-LAB']['labinsec']
        except KeyError:
            return None

        try:
            labinsec = LabInSection.objects.get(id=session_labinsec_id)
            da = DirectToLabAccount.objects.get(
                    user=request.user,
                    labinsec=labinsec)
            if da.enabled:
                return labinsec
            else:
                raise Exception('This direct-to-lab account is disabled.')
        except DirectToLabAccount.DoesNotExist:
            raise Exception('This direct-to-lab account no longer exists.')
        except LabInSection.DoesNotExist:
            raise Exception('The designated lab no longer exists.')

    def passes_direct_to_lab(self, request):
        """
        Check whether the request meets direct-to-lab policy
        """
        try:
            da = DirectToLabAccount.objects.get(user=request.user,labinsec=self)
            if da.enabled:
                session_labinsec_id = request.session['DIRECT-TO-LAB']['labinsec']
                return self.id == session_labinsec_id
            else:
                return False
        except KeyError: # not logged in with direct-to-lab account
            return False
        except DirectToLabAccount.DoesNotExist:
            return True

    def direct_to_lab_submission_allowed(self, request):
        """
        Check whether the requesting user is allowed to submit an answer using
        direct-to-lab account
        """
        try:
            da = DirectToLabAccount.objects.get(user=request.user,labinsec=self)
            if da.enabled:
                session_labinsec_id = request.session['DIRECT-TO-LAB']['labinsec']
                return self.id == session_labinsec_id and da.submission_allowed
            else:
                return False
        except KeyError: # not logged in with direct-to-lab account
            pass
        except DirectToLabAccount.DoesNotExist:
            pass
        return False


class Submission(models.Model):
    """
    Submission model keeps students' submission with grading result.

    """
    # Constants for grading status
    CODE_STATUS_INQUEUE = 1
    CODE_STATUS_GRADING = 2
    CODE_STATUS_GRADED = 3

    assignment = models.ForeignKey(Assignment,on_delete=models.CASCADE)
    section = models.ForeignKey(Section,blank=True,null=True,on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)

    # answer stores a dict indexed by blank id (zero offset, e.g., 0,
    # 1, ...)
    answer = AnswerField()

    # results stores code grading result as a Boolean list.
    results = GradingResultField()

    compiler_messages = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True,db_index=True)
    remote_addr = models.CharField(max_length=40, blank=True, default='')
    start_grading_at = models.DateTimeField(blank=True, null=True)
    graded_at = models.DateTimeField(blank=True, null=True)
    code_grading_status = models.IntegerField(default=CODE_STATUS_GRADED)

    # manual_scores keeps a dict of integer indexed by blank id (as
    # string, e.g., "b1", "b2", ...)
    manual_scores = JSONField(blank=True, null=True)

    def __str__(self):
        return "Submitted at {} by user-id:{} sec-id:{}".format(self.submitted_at, self.user_id, self.section_id)

    def graded(self):
        return self.code_grading_status == Submission.CODE_STATUS_GRADED

    def passed(self):
        if not self.graded():
            return False

        for r in self.results:
            if not r.passed():
                return False
        return True

    def partial_code_score(self):
        if not self.graded():
            return 0

        s = 0
        t = 0
        for r in self.results:
            if r.passed():
               s += 1
            t += 1
        if t!=0:
            return float(s)/t
        else:
            return 0

    def html(self):
        template = self.assignment.task.html_template
        answer_fields = {}
        for i in self.answer.keys():
            answer_fields["b%d" % (i+1)] = self.answer[i]
        template = Template(template)
        context = Context(answer_fields)
        try:
            return template.render(context)
        except:
            return "Rendering error"

    def sum_manual_scores(self):
        if self.manual_scores:
            return sum(self.manual_scores.values())
        else:
            return 0

    def manual_grading_completed(self):
        notgraded = set(['b'+str(x['id']) for x in self.assignment.task.textblanks])
        if self.manual_scores:
            for blank_id in self.manual_scores.keys():
                try:
                    notgraded.remove(blank_id)
                except KeyError:
                    pass
        return len(notgraded)==0

    def make_task_concrete(self):
        # in case of super-task submission, resolve for concrete task
        if hasattr(self,'assignment') and hasattr(self,'user') and \
                not self.assignment.task.is_concrete():
            self.assignment.make_task_concrete_for_user(
                    self.user,self.section)

    @staticmethod
    def get_recent_for_user_and_section(user, section):
        all_submissions = user.submission_set.filter(section=section).reverse()
        assignment_ids = {}
        submissions = []
        for sub in all_submissions:
            if sub.assignment.id not in assignment_ids:
                submissions.append(sub)
                assignment_ids[sub.assignment.id] = True
        return submissions

    @staticmethod
    def fetch_one_inqueue_submission(use_transaction=True):
        if use_transaction:
            from django.db import connection

            cursor = connection.cursor()
            cursor.execute("START TRANSACTION;")
            num = cursor.execute("SELECT id from lab_submission WHERE code_grading_status=%d ORDER BY submitted_at LIMIT 1 FOR UPDATE;" % (Submission.CODE_STATUS_INQUEUE,))
            if num==1:
                submission_id = cursor.fetchone()[0]
                cursor.execute("UPDATE lab_submission SET code_grading_status=%d WHERE id=%d;" % (Submission.CODE_STATUS_GRADING, submission_id))
            else:
                submission_id = None
            cursor.execute("COMMIT;")
            if submission_id!=None:
                return Submission.objects.get(id=submission_id)
            else:
                return None
        else:
            submissions = (
                Submission.objects
                .filter(code_grading_status=Submission.CODE_STATUS_INQUEUE)
                .order_by("submitted_at")
                .all()[:1])
            if len(submissions)==1:
                return submissions[0]
            else:
                return None

    @staticmethod
    def count_inqueue_submissions():
        return (Submission.objects
                .filter(code_grading_status=Submission.CODE_STATUS_INQUEUE)
                .count())

    def status_summary(self):
        status = {
            'graded': self.graded(),
            'passed': self.passed(),
            'results': ''.join([str(r) for r in self.results]),
            'compiler_messages': self.compiler_messages,
            'submitted_at': timezone.localtime(self.submitted_at).strftime("%Y-%m-%d %H:%M:%S"),
            'remote_addr': self.remote_addr,
            'manual_scores': self.manual_scores,
        }
        return status

    class Meta:
        ordering = ['submitted_at']


ADDR_LIST_HELP_TEXT = mark_safe(
    "Enter a single IP (e.g., <tt style='color:green'>158.108.32.8</tt>) "
    "or an IP range (e.g., <tt style='color:green'>10.16.5.0 - 10.16.5.255</tt>) in each line.<br/>"
    "An empty line or a line starting with <tt style='color:green'>#</tt> will be ignored, but will still be saved."
)

class AddressAcl(models.Model):
    '''Access control list based on IP addresses'''
    labinsec = models.OneToOneField(LabInSection,on_delete=models.CASCADE)
    allowed_list = models.TextField(blank=True,null=True,help_text=ADDR_LIST_HELP_TEXT)
    denied_list = models.TextField(blank=True,null=True,help_text=ADDR_LIST_HELP_TEXT)
    default_action = models.CharField(max_length=2,default='d',choices=[
        ('a','allow'),
        ('d','deny'),
        ])
    activated = models.BooleanField(default=True)
    pickled_allowed_list = models.BinaryField()
    pickled_denied_list = models.BinaryField()
    single_ip = models.BooleanField(default=False, verbose_name="Enforce Single IP")

    class Meta:
        verbose_name = "Address ACL"

    def __str__(self):
        return "ACL for {} - {}".format(
                self.labinsec,
                "ACTIVE" if self.activated else "INACTIVE",
                )

    def clean(self):
        try:
            alist = parse_address_list(self.allowed_list)
            self.pickled_allowed_list = pickle.dumps(alist)
        except Exception as e:
            raise ValidationError({ 'allowed_list': str(e) })

        try:
            dlist = parse_address_list(self.denied_list)
            self.pickled_denied_list = pickle.dumps(dlist)
        except Exception as e:
            raise ValidationError({ 'denied_list': str(e) })

    def get_allowed_list(self):
        if len(self.pickled_allowed_list) == 0:
            return []
        else:
            return pickle.loads(self.pickled_allowed_list)

    def get_denied_list(self):
        if len(self.pickled_denied_list) == 0:
            return []
        else:
            return pickle.loads(self.pickled_denied_list)


class SingleIpLock(models.Model):
    '''Keep track of IP address used by user to access a lab in section.
    This model is used in conjunction with single-IP restriction flag in the
    model AddressAcl'''
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    labinsec = models.ForeignKey(LabInSection,
            on_delete=models.CASCADE,
            verbose_name="Lab in Section")
    ip = models.GenericIPAddressField(verbose_name="IP Address")
    last_access = models.DateTimeField()

    class Meta:
        unique_together = [  # also imply index_together
            ("user","labinsec"),
        ]
        verbose_name = "Single IP Lock"

    def __str__(self):
        return "{} from {} accessing <{}>".format(
                self.user,
                self.ip,
                self.labinsec,
                )


class DirectToLabAccount(models.Model):
    """
    Provide a temporary account for a user to directly access a lab in
    section.  If exists, the specified user MUST use the provided
    username/password to log in in order to access the specified lab.
    """

    RANDOM_CHARS = "ACDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz2345679"
    ACCOUNT_CODE_LENGTH = 5
    PASSWORD_LENGTH = 5
    ACCOUNT_PREFIX = "elab-"

    username = models.CharField(max_length=20,unique=True)
    password = models.CharField(max_length=20)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    labinsec = models.ForeignKey(LabInSection,on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False)
    submission_allowed = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'direct-to-lab account'
        unique_together = (
                ('user','labinsec'),
                )

    def __str__(self):
        return "{}:{}".format(self.username,self.password)


    @staticmethod
    def generate(user,labinsec):
        '''generate a unique direct-to-lab account with a random password'''

        def get_random_word(length):
            p = [random.choice(DirectToLabAccount.RANDOM_CHARS)
                    for i in range(length)]
            return ''.join(p)

        while True:
            username = DirectToLabAccount.ACCOUNT_PREFIX + \
                    get_random_word(DirectToLabAccount.ACCOUNT_CODE_LENGTH)
            if not DirectToLabAccount.objects.filter(username=username).exists():
                break
        passwd = get_random_word(DirectToLabAccount.PASSWORD_LENGTH)

        try:
            da = DirectToLabAccount.objects.get(user=user,labinsec=labinsec)
        except DirectToLabAccount.DoesNotExist:
            da = DirectToLabAccount(user=user,labinsec=labinsec)
        da.username = username
        da.password = passwd
        da.enabled = True
        da.submission_allowed = False
        da.save()
        return da
