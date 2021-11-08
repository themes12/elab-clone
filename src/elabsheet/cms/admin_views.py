import os
import random
from copy import deepcopy
from datetime import date, datetime
import json

from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.urls import reverse, get_script_prefix
from django import forms
from django.template import RequestContext, Template, Context
from django.contrib import messages

from .models import Course, Task, Lab, Assignment, ChildTask, CachedChildTask
from lab.models import Submission
from lab.views import build_answer
from commons.utils import staff_check
from commons.utils import find_extension

@login_required
@user_passes_test(staff_check)
def get_sol(request,task_id):
    #if not request.user.is_staff:
    #    return HttpResponseForbidden()
    task = get_object_or_404(Task, pk=task_id)
    ext = find_extension(task.language)
    response = HttpResponse(task.solution(), 'text/plain')
    response['Content-Disposition'] = 'attachment; filename=source.%s' % ext
    return response


@login_required
@user_passes_test(staff_check)
def preview_task(request):
    """
    Returns task html content for previewing in task change form
    (returned from ajax request).

    """
    if request.method == 'POST':
        source = request.POST.get('source')
        lang   = request.POST.get('language')
    else:
        source = request.GET.get('source')
        lang   = request.GET.get('language')
    html,textblanks = Task.build_html_from_source(source,lang)
    sols = [("b%d"%i,s,p) for (i,(s,p)) in textblanks.items()]
    return HttpResponse(json.dumps({
        #"html" : render_to_string('admin/cms/task/preview.html', {
        #    "task_html":html}),
        "html" : html,
        "sols" : sols,
        }))


@login_required
@user_passes_test(staff_check)
def new_task_version(request,task_id):
    task = get_object_or_404(Task, pk=task_id)

    new_task = deepcopy(task)

    disable_note = (' (version %d, disabled on %s)' % 
                    (task.version, date.today().strftime('%d %b %y')))
    task.name = task.name + disable_note
    task.note = (task.note + disable_note).strip()
    task.disabled = True
    task.save()

    new_task.id = None
    new_task.version = task.version + 1
    new_task.save()

    for assignment in task.assignment_set.all():
        assignment.task = new_task
        assignment.save()

    return HttpResponseRedirect(get_script_prefix() + 
                                ('admin/cms/task/%s/' % new_task.id))

def create_clonded_task(task, user=None):
    cloned_task = deepcopy(task)
    cloned_task.id = None
    cloned_task.version = 1
    cloned_task.name = cloned_task.name + ' (cloned)'
    cloned_task.creator = user
    cloned_task.owner = user
    if not user:
        cloned_task.note = (cloned_task.note + ' (cloned)').strip()
    else:
        cloned_task.note = (cloned_task.note + 
                            ' (cloned by ' +
                            user.username + ')').strip()
    cloned_task.save()

    # also clone all grading supplements
    for sup in task.supplement_set.all():
        new_sup = sup.clone()
        new_sup.task = cloned_task
        new_sup.save()

    return cloned_task

@login_required
@user_passes_test(staff_check)
def clone_task(request,task_id):
    task = get_object_or_404(Task, pk=task_id)
    cloned_task = create_clonded_task(task, request.user)
    messages.success(request, "Task cloned successfully")
    return HttpResponseRedirect(get_script_prefix() + 
                                ('admin/cms/task/%s/' % cloned_task.id))


@login_required
@user_passes_test(staff_check)
def test_task(request,task_id):
    task = get_object_or_404(Task, pk=task_id)
    title = "Test Task: %s" % (task)
    is_supertask = task.is_supertask()
    if is_supertask:
        try:
            seed = int(request.GET.get('seed',0))
        except ValueError:
            seed = 0
        try:
            diff = int(request.GET.get('diff',0))
        except ValueError:
            diff = 0
        try:
            seed,diff = request.GET['key'].split(':')
        except ValueError:
            seed,diff = 0,0
        except KeyError:
            pass
        task.make_concrete(seed,diff)
    else:
        seed = None
        diff = None

    cached_count = CachedChildTask.objects.filter(parent_task=task).count()

    if request.method=='GET':
        try:
            if request.GET['action'] == 'Random':
                seed = random.randrange(0,10000)
                diff = random.randrange(0,10)
                url = reverse('cms:admin-cms-task-test',args=[task.id]) \
                        + '?seed={}&diff={}'.format(seed,diff)
                return redirect(url)
        except KeyError:
            pass
        return render(request, 'admin/cms/task/test.html',
                {
                    'title' : title,
                    'task' : task,
                    'seed' : seed,
                    'diff' : diff,
                    'is_supertask' : is_supertask,
                    'cached_count' : cached_count,
                })
    elif request.method=='POST':
        answer = build_answer(request.POST.items(),request.FILES.items())
        grading_results = task.verify(answer)
        result_list = [r['passed'] for r in grading_results]
        manual_grading_results = task.verify_manual_auto_gradable_fields(answer)
        submission = Submission(assignment=Assignment(lab=None,task=task),
                                user=request.user,
                                answer=answer,
                                results=result_list,
                                manual_scores=manual_grading_results,
                                submitted_at=datetime.now())
        testcases = task.testcases
        results = zip(testcases,submission.results)
        submission.prerendered_results = render_to_string(
                'lab/include/explained_results.html',
                { 'submission' : submission, 'results' : results })
        return render(request, 'admin/cms/task/test.html',
                {
                    'title' : title,
                    'task' : task,
                    'seed' : seed,
                    'diff' : diff,
                    'is_supertask' : is_supertask,
                    'cached_count' : cached_count,
                    'submission' : submission,
                    'manual_scores_json' : json.dumps(submission.manual_scores),
                })


@login_required
@user_passes_test(staff_check)
def preview_task_as_iframe(request):
    return render(request, 'admin/cms/task/preview.html', {})

@login_required
@user_passes_test(staff_check)
def preview_childtask_as_iframe(request,parent_task_id,key):
    task = Task.objects.get(id=parent_task_id)
    seed,difficulty = key.split(':')
    task.make_concrete(int(seed),int(difficulty))
    return render(request, 'admin/cms/cachedchildtask/preview.html', {
        'task' : task,
        'sols' : json.dumps(task.textblanks),
        })


def task_syntax_help(request):

    from django.conf import settings

    media_url = settings.MEDIA_URL

    file_path = os.path.abspath(os.path.dirname(__file__))
    help_index_lines = open(os.path.join(file_path,
                                         'docs/index')).readlines()
    help_tabs = []
    for line in help_index_lines:
        items = line.strip().split(',')
        if len(items)==2:
            doc = open(os.path.join(file_path,
                                    'docs/'+items[1])).read()
            try:
                t = Template(doc)
                doc = t.render(Context({"media_url": media_url}))
            except:
                pass

            help_tabs.append({'title': items[0],
                              'body': doc})

    return render(request, 'admin/cms/task/help.html',
            {
                'title' : 'Source syntax help',
                'is_popup' : True,
                'help_tabs' : help_tabs,
            })

@login_required
@user_passes_test(staff_check)
def clone_lab(request,lab_id,deepclone=False):
    lab = get_object_or_404(Lab, pk=lab_id)
    assignments = lab.assignment_set.all()

    cloned_lab = Lab()
    cloned_lab.name = lab.name + ' (cloned)'
    cloned_lab.tags = lab.tags
    cloned_lab.disabled = lab.disabled
    cloned_lab.save()
    
    for a in assignments:
        if deepclone:
            ct = create_clonded_task(a.task, request.user)
            ct.owner = request.user
            ct.save()
        else:
            ct = a.task

        ca = Assignment()
        ca.lab = cloned_lab
        ca.task = ct
        ca.number = a.number
        ca.save()

    if deepclone:
        messages.success(request, "Lab deep-cloned successfully")
    else:
        messages.success(request, "Lab cloned successfully")
    return HttpResponseRedirect(get_script_prefix() + 
                                ('admin/cms/lab/%s/' % cloned_lab.id))


@login_required
@user_passes_test(staff_check)
def deepclone_lab(request,lab_id):
    return clone_lab(request,lab_id,deepclone=True)

#
# Forms for task/lab search and selection
#

class TaskReadOnlyInput(forms.HiddenInput):
    def render(self, name, value, attrs=None):
        if value!=None and value!='':
            task_name = str(Task.objects.get(pk=value))
        else:
            task_name = ''
        return mark_safe(task_name + 
                         super(TaskReadOnlyInput, self).
                         render(name, value, attrs))

class AssignmentFormMock(forms.Form):
    """
    AssignmentFormMock is used to generate an extra form for
    AdminFormMock when new task is added to a lab.
    """
    id = forms.IntegerField(widget=forms.HiddenInput)
    number = forms.CharField(max_length=20,
                             widget=forms.TextInput)
    task = forms.ModelChoiceField(queryset=Task.objects,
                                  widget=TaskReadOnlyInput)
    lab = forms.ModelChoiceField(queryset=Lab.objects,
                                 widget=forms.HiddenInput)


class LabReadOnlyInput(forms.HiddenInput):
    def render(self, name, value, attrs=None):
        if value!=None and value!='':
            lab_name = str(Lab.objects.get(pk=value))
        else:
            lab_name = ''
        return mark_safe(lab_name + 
                         super(LabReadOnlyInput, self).
                         render(name, value, attrs))

class LabInCourseFormMock(forms.Form):
    """
    LabInCourseFormMock is used to generate an extra form for
    AdminFormMock when new lab is added to a course.
    """
    id = forms.IntegerField(widget=forms.HiddenInput)
    number = forms.CharField(max_length=20,
                             widget=forms.TextInput)
    lab = forms.ModelChoiceField(queryset=Lab.objects,
                                 widget=LabReadOnlyInput)
    course = forms.ModelChoiceField(queryset=Course.objects,
                                    widget=forms.HiddenInput)

