import json
from datetime import datetime
import csv
import codecs

from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.urls import reverse

from django.forms import ModelForm, Textarea, TextInput, Select
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string

from django.contrib.auth.models import User

from .models import TaskPad, TaskPost, Participant
from .utils import make_result_explanation
from cms.models import Task, Assignment
from lab.models import Submission
from lab.views import build_answer
from logger.models import Log
from commons.decorators import taskpads_required
from commons.utils import get_remote_addr_from_request

def create_new_task_pad_and_redirect(creator=None):
    task_pad = TaskPad.create_for(creator)
    if task_pad:
        return redirect(reverse('taskpads:change', args=[task_pad.access_key,
                                                         task_pad.secret_key]))
    else:
        raise Exception('Task pad saving error')

    
@taskpads_required
def create_new_task_post_and_redirect(request,task_pad):
    if request.user.is_authenticated:
        creator = request.user
    else:
        creator = None
    post = TaskPost.create_for(task_pad, creator)
    return redirect(reverse('taskpads:editpost', args=[post.key]))


@taskpads_required
def index(request):
    if not request.user.is_authenticated:
        return create_new_task_pad_and_redirect()
    task_pads = TaskPad.objects.filter(creator=request.user).all()
    return render(request,
                  'taskpads/index.html',
                  { 'task_pads': task_pads })


@taskpads_required
def new(request):
    if not request.user.is_authenticated:
        return create_new_task_pad_and_redirect()
    else:
        return create_new_task_pad_and_redirect(request.user)

    
class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ['name',
                  'language',
                  'source']
        widgets = {
            'name': TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'ชื่อโจทย์',
            }),
            'language': Select(attrs={'class': 'form-control'}),
            'source': Textarea(attrs={'class': 'form-control'}),
        }

        
@taskpads_required
def change(request, access_key, secret_key):
    task_pad = get_object_or_404(TaskPad,
                                 access_key=access_key)
    if task_pad.secret_key != secret_key:
        raise PermissionDenied

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task_pad.task)
        if form.is_valid():
            task = form.save()
            task_pad.task = task
            task_pad.updated_at = timezone.now()
            task_pad.save()
    else:
        form = TaskForm(instance=task_pad.task)

    url = request.build_absolute_uri(reverse('taskpads:change',args=[
        task_pad.access_key,
        task_pad.secret_key ]))

    return render(request,
                  'taskpads/change.html',
                  { 'task_pad': task_pad,
                    'form': form,
                    'url': url})


@taskpads_required
def manage(request, access_key, secret_key):
    task_pad = get_object_or_404(TaskPad,
                                 access_key=access_key)
    if task_pad.secret_key != secret_key:
        raise PermissionDenied

    task_posts = task_pad.task_posts.all()

    active_post_key = request.GET.get('key','')
    post_form_visible = request.GET.get('post_form','') == 'true'

    if active_post_key == '':
        if len(task_posts)!=0:
            task_posts[0].is_active = True
    else:
        for task_post in task_posts:
            if task_post.key == active_post_key:
                task_post.is_active = True
    
    return render(request,
                  'taskpads/manage.html',
                  { 'task_pad': task_pad,
                    'task_posts': task_posts,
                    'active_post_key': active_post_key,
                    'post_form_visible': post_form_visible })


@taskpads_required
def create_post(request, access_key, secret_key):
    task_pad = get_object_or_404(TaskPad,
                                 access_key=access_key)
    if task_pad.secret_key != secret_key:
        raise PermissionDenied

    if request.method == 'POST':
        return create_new_task_post_and_redirect(request,task_pad)
    else:
        raise PermissionDenied

    
@taskpads_required
def preview(request):
    if request.method == 'POST':
        source = request.POST.get('source')
        lang   = request.POST.get('language')
    else:
        source = request.GET.get('source')
        lang   = request.GET.get('language')
    html, textblanks = Task.build_html_from_source(source, lang)
    sols = [("b%d" % i,s,p) for (i,(s,p)) in textblanks.items()]

    return HttpResponse(json.dumps({
        "html" : html,
        "sols" : sols,
    }), content_type="application/json")

@taskpads_required
def preview_iframe(request):
    return render(request,
                  'taskpads/preview_iframe.html')

@taskpads_required
def test_task(request, access_key, secret_key):
    task_pad = get_object_or_404(TaskPad,
                                 access_key=access_key)
    if task_pad.secret_key != secret_key:
        raise PermissionDenied

    if request.method!='POST':
        raise PermissionDenied
        
    task = task_pad.task
    if not task:
        raise PermissionDenied

    from lab.views import build_answer
    from lab.models import Submission

    answer = build_answer(request.POST.items(),
                          request.FILES.items())
    
    grading_results = task.verify(answer)
    result_list = [r['passed'] for r in grading_results]
    manual_grading_results = task.verify_manual_auto_gradable_fields(answer)
    submission = Submission(assignment=Assignment(lab=None,task=task),
                            answer=answer,
                            results=result_list,
                            manual_scores=manual_grading_results,
                            submitted_at=datetime.now())
    testcases = task.testcases
    results = zip(testcases,submission.results)
    
    submission.prerendered_results = render_to_string(
        'lab/include/explained_results.html',
        { 'submission' : submission, 'results' : results })

    res_data = {
        'results': [str(r) for r in submission.results],
        'detailed': submission.prerendered_results,
    }
    return HttpResponse(json.dumps(res_data),
                        content_type="application/json")


class TaskPostForm(ModelForm):
    class Meta:
        model = TaskPost
        fields = ['participants','enabled']
        widgets = {
            'participants': Textarea(attrs={
                'class': 'form-control',
                'placeholder': '# ป้อนชื่อผู้เรียนบรรทัดละหนึ่งชื่อ\n'
                               '# ระบบจะไม่สนใจบรรทัดว่างหรือบรรทัดที่ขึ้นต้นด้วย #',
                }),
        }
    
@taskpads_required
def edit_post(request, post_key):
    post = get_object_or_404(TaskPost, key=post_key)

    if request.method == 'POST':
        form = TaskPostForm(request.POST, instance=post)
        if form.is_valid():
            messages.success(request, "Task post saved successfully")
            post = form.save()
            return redirect(reverse('taskpads:manage',
                                    args=[post.task_pad.access_key,
                                          post.task_pad.secret_key]) +
                            '?key=' + post.key)
    else:
        form = TaskPostForm(instance=post)

    return render(request, 'taskpads/task_post.html', {
        'post': post,
        'form': form,
    })

@taskpads_required
def render_task_pad_for_submission(request,
                                   post,
                                   task_pad,
                                   task,
                                   participant,
                                   recent_submission,
                                   is_anonymous=False,
                                   share_key=None):
    return render(request, 'taskpads/workon.html', {
        'post' : post,
        'task_pad': task_pad,
        'task': task,
        'participant': participant,
        'recent_submission': recent_submission,
        'is_anonymous': is_anonymous,
        'share_key': share_key,
    })


@taskpads_required
def clone(request, access_key, share_key):
    task_pad = get_object_or_404(TaskPad,
                                 access_key=access_key)

    share_key = request.GET.get('sharing',None)

    if share_key and share_key != task_pad.get_share_key():
        return HttpResponse(status=403)

    if request.method == 'POST':
        if request.user.is_authenticated:
            creator = request.user
        else:
            creator = None
        new_task_pad = TaskPad.clone(task_pad,
                                     creator,
                                     'taskpad task clone from pad: %d' % (task_pad.id,))
        return HttpResponse(json.dumps({ 'access_key': new_task_pad.access_key,
                                         'secret_key': new_task_pad.secret_key, }),
                            content_type="application/json")
    else:
        return HttpResponse(status=403)

    
@taskpads_required
def show(request, access_key):
    task_pad = get_object_or_404(TaskPad,
                                 access_key=access_key)

    share_key = request.GET.get('sharing',None)

    if share_key and share_key != task_pad.get_share_key():
        return HttpResponse(status=403)

    task = task_pad.task
    post = TaskPost(key=task_pad.access_key)
    participant = Participant(key=settings.TASKPADS_ANONYMOUS_PARTICIPANT_KEY)
    recent_submission = None
    
    return render_task_pad_for_submission(request,
                                          post,
                                          task_pad,
                                          task,
                                          participant,
                                          recent_submission,
                                          True,
                                          share_key)


@taskpads_required
def workon(request, post_key, participant_key):
    post = get_object_or_404(TaskPost, key=post_key)
    participant = get_object_or_404(Participant, key=participant_key)

    assignment = post.task_pad.get_assignment()
    recent_submission = assignment.get_recent_submission_for_user(participant.user,None)
    if recent_submission:
        status = recent_submission.status_summary()
        status['result_explanation'] = make_result_explanation(recent_submission)
        recent_submission.json_status = json.dumps(status)

    return render_task_pad_for_submission(request,
                                          post,
                                          post.task_pad,
                                          post.task_pad.task,
                                          participant,
                                          recent_submission)


@taskpads_required
def ajax_submit(request, post_key, participant_key):
    if participant_key == settings.TASKPADS_ANONYMOUS_PARTICIPANT_KEY:
        is_anonymous = True
        task_pad = get_object_or_404(TaskPad,
                                     access_key=post_key)
        task = task_pad.task
        user,_ = User.objects.get_or_create(username=settings.TASKPADS_ANONYMOUS_SUBMISSION_USERNAME)
    else:
        is_anonymous = False
        post = get_object_or_404(TaskPost, key=post_key)
        participant = get_object_or_404(Participant, key=participant_key)
        task_pad = post.task_pad
        task = task_pad.task
        user = participant.user

    remote_addr = get_remote_addr_from_request(request)

    answer = build_answer(request.POST.items(),request.FILES.items())
    assignment = task_pad.get_assignment()
    submission = Submission(assignment=assignment,
                            section=None,
                            user=user,
                            answer=answer,
                            remote_addr=remote_addr)

    if settings.SEPARATE_GRADING:
        submission.code_grading_status = Submission.CODE_STATUS_INQUEUE
    else:
        grading_results, messages = task.verify_with_messages(answer)
        manual_grading_results = task.verify_manual_auto_gradable_fields(answer)

        result_list = [r['passed'] for r in grading_results]
        submission.compiler_messages = messages
        submission.results = result_list
        submission.manual_scores = manual_grading_results
        submission.graded_at = datetime.now()

    submission.save()

    if not is_anonymous:
        Log.create("taskpads:submit", request,
                   comment=("id: %d, taskpad-id:%d post-id:%d" % 
                            (submission.id, task_pad.id, post.id)))
    else:
        Log.create("taskpads:submit", request,
                   comment=("id: %d, taskpad-id:%d anonymous" % 
                            (submission.id, task_pad.id)))
        

    return JsonResponse({
        'submission_id' : submission.id,
        })

@taskpads_required
def ajax_submission_status(request, participant_key, submission_id):
    if participant_key == settings.TASKPADS_ANONYMOUS_PARTICIPANT_KEY:
        participant = None
    else:
        participant = get_object_or_404(Participant, key=participant_key)
        
    submission = get_object_or_404(Submission, id=submission_id)

    if participant:
        if participant.user_id != submission.user_id:
            raise Http404
    elif submission.user.username != settings.TASKPADS_ANONYMOUS_SUBMISSION_USERNAME:
        raise Http404

    status = submission.status_summary()
    status['result_explanation'] = make_result_explanation(submission)

    return JsonResponse(status)

@taskpads_required
def post_export_txt(request, post_key):
    post = get_object_or_404(TaskPost, key=post_key)
    response = HttpResponse(content_type='text/plain; charset=utf-8')
    response.write('\t'.join(['No','Name','Link','SubmittedAt','Result','Details']) + '\n')
    for i,participant in enumerate(post.participant_set.all()):
        status = participant.latest_submission_status()
        submitted_at = ''
        result = ''
        details = ''
        if status:
            submitted_at = str(status['submitted_at'])
            if status['graded']:
                if status['passed']:
                    result = 'Passed'
                else:
                    result = 'Failed'
                details = status['results']
            else:
                result = 'Grading'
        link = request.build_absolute_uri(reverse('taskpads:workon',
            args=[post.key,participant.key]))
        response.write('\t'.join([str(i+1),participant.name,link,submitted_at,result,details]) + '\n')
    return response

@taskpads_required
def post_export_csv(request, post_key):
    post = get_object_or_404(TaskPost, key=post_key)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
            'attachment; filename=group-{}.csv'.format(post.key)
    response.write(codecs.BOM_UTF8)
    writer = csv.writer(response, dialect='excel')
    writer.writerow(['No','Name','Link','SubmittedAt','Result','Details'])
    for i,participant in enumerate(post.participant_set.all()):
        link = request.build_absolute_uri(reverse('taskpads:workon',
            args=[post.key,participant.key]))
        status = participant.latest_submission_status()
        submitted_at = ''
        result = ''
        details = ''
        if status:
            submitted_at = str(status['submitted_at'])
            if status['graded']:
                if status['passed']:
                    result = 'Passed'
                else:
                    result = 'Failed'
                details = status['results']
            else:
                result = 'Grading'
        writer.writerow([i+1,participant.name,link,submitted_at,result,details])
    return response
