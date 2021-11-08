import re
import datetime
import json
import functools

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, \
        HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.urls import reverse
from django import template

from commons.decorators import ajax_login_required
from commons.utils import get_svn_revision, get_remote_addr_from_request
from cms.models import Lab, Assignment
from .models import Submission, Section, LabInSection, DirectToLabAccount
from logger.models import Log

MSG_LAB_CLOSED = \
    'This lab has been closed.'
MSG_READONLY = \
    'This lab is read only.'
MSG_ACL = \
    'This lab cannot be accessed from your current location.'
MSG_DIRECT_TO_LAB_REQUIRED = \
    'You must log in using the direct-to-lab account to access this lab.'
MSG_NOT_ENROLLED = \
    'You are not enrolled in this section'
MSG_NOT_OWNER = \
    'This is not your submission'
MSG_LAB_NOT_IN_SEC = \
    'This lab does not belong to this section'

def error_page(request, message):
    return HttpResponseForbidden(
        template.loader.render_to_string('lab/error.html', {
            'message' : message,
        }))


def check_direct_to_lab(view_func):
    """
    Decorator for views that must be redirected to the designated lab when a
    direct-to-lab account is used.
    """
    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # if logged in using a direct-to-lab account, redirect the user to
        # the corresponding lab right away
        try:
            labinsec = LabInSection.get_direct_to_lab(request)
            if labinsec:
                return redirect("lab:show-lab",
                        sec_id=labinsec.section_id,
                        labinsec_id=labinsec.id)
        except Exception as e:
            return error_page(request,str(e))
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
@check_direct_to_lab
def index(request):
    teaches_active = Section.objects.filter(instructors=request.user,active=True)
    teaches_inactive = Section.objects.filter(instructors=request.user,active=False)
    learns_active  = Section.objects.filter(students=request.user,active=True)
    learns_inactive  = Section.objects.filter(students=request.user,active=False)

    # get svn revision, for development
    try:
        if settings.SHOW_SVN_REVISION:
            revision = get_svn_revision()
        else:
            revision = None
    except:
        revision = None

    return render(request, 'lab/index.html', 
            { 
                'teaches_active': teaches_active,
                'teaches_inactive': teaches_inactive,
                'learns_active': learns_active,
                'learns_inactive': learns_inactive,
                'svn_revision': revision
            })


def get_section_statistic_for_user(user, section, labs):
    recent_submissions = Submission.get_recent_for_user_and_section(user, 
                                                                    section)
    stat_dict = {}
    for lab in labs:
        assignments = lab.assignment_set.all()
        assignment_total = len(assignments)
        manual_total = sum([assignment.task.manual_full_score() 
                             for assignment in assignments])
        stat_dict[lab.id] = {'passed': 0, 
                             'submitted': 0, 
                             'total': lab.assignment_set.count(),
                             'manual_total': manual_total,
                             'manual_score': 0}
    for submission in recent_submissions:
        if submission.assignment.lab.id in stat_dict:
            stat_dict[submission.assignment.lab.id]['submitted'] += 1
            if submission.passed():
                stat_dict[submission.assignment.lab.id]['passed'] += 1
            stat_dict[submission.assignment.lab.id]['manual_score'] += submission.sum_manual_scores()
    return [ stat_dict[lab.id] for lab in labs ]


@login_required
@check_direct_to_lab
def list_labs(request,sec_id):
    user = request.user

    section = get_object_or_404(Section, pk=sec_id)
    if not section.has_student(user):
        return error_page(request, MSG_NOT_ENROLLED)

    labset = section.labinsection_set.all()

    # extract all labs for this section except those associated with a
    # direct-to-lab account
    labs = list(labset)
    for lab in labs:
        lab.direct_to_lab_required = not lab.passes_direct_to_lab(request)

    # This status query takes too many database hits; disable it for now
    #statuses = get_section_statistic_for_user(user, section, labs)    
    statuses = [None] * len(labs)

    return render(request, 'lab/labs.html', 
            {
                'labs_with_statuses' : zip(labs,statuses), 
                'sec' : section 
            })


@login_required
def show_lab(request,sec_id,labinsec_id,cur_assignment_id=None):
    labinsec = get_object_or_404(LabInSection, pk=labinsec_id)
    da_submission_allowed = labinsec.direct_to_lab_submission_allowed(request)
    if labinsec.disabled and not da_submission_allowed:
        return error_page(request, MSG_LAB_CLOSED)
    if not labinsec.passes_address_acl(request):
        return error_page(request, MSG_ACL)
    if not labinsec.passes_direct_to_lab(request):
        return error_page(request, MSG_DIRECT_TO_LAB_REQUIRED)

    sec = get_object_or_404(Section, pk=sec_id)
    lab = labinsec.lab
    user = request.user

    if not sec.has_student(user):
        return error_page(request, MSG_NOT_ENROLLED)
    if sec != labinsec.section:
        return error_page(request, MSG_LAB_NOT_IN_SEC)

    hidden_tasks = set(int(x.strip()) for x in labinsec.hidden_tasks.split(",")
                                      if x.isdigit())
    assignments = [a for a in lab.assignment_set.all() 
            if a.id not in hidden_tasks]
    submissions = []
    for assignment in assignments:
        assignment.make_task_concrete_for_user(user,sec)
        submission = assignment.get_recent_submission_for_user(user,sec)
        submissions.append(submission)

    assignments_with_submissions = list(zip(assignments, submissions))

    all_manual_scores = json.dumps(
            {submission.id:submission.manual_scores
                for (assignment,submission) in assignments_with_submissions
                if submission
            })

    # current assignment 
    if cur_assignment_id != None:
        cur_assignment = get_object_or_404(Assignment, pk=cur_assignment_id)
        cur_assignment.make_task_concrete_for_user(user,sec)
    else:
        if len(assignments)>0:
            cur_assignment = assignments[0]
        else:
            cur_assignment = None

    # recent submission
    if cur_assignment != None:
        recent_submission = cur_assignment.get_recent_submission_for_user(user,sec)
        if recent_submission is not None and settings.LOG_SUBMISSION_ACCESS:
            Log.create("access", request,
                       comment=("id: %d, task-id: %d, sect-id: %s" % (
                           recent_submission.id,
                           recent_submission.assignment.task_id,
                           recent_submission.section.id)))
    else:
        recent_submission = None

    return render(request, 'lab/show.html', 
            {
                'sec': sec,
                'lab': lab,
                'labinsec': labinsec,
                'assignments': assignments_with_submissions,
                'cur_assignment': cur_assignment,
                'recent_submission': recent_submission,
                'all_manual_scores': all_manual_scores,
                'da_submission_allowed': da_submission_allowed,
                'is_instructor': sec.has_instructor(user),
            })


def build_answer(items, file_items=None):
    """
    This function takes all request params whose keys match /b\d+/
    and returns all params as a dictionary.

    >>> build_answer([('a','100'),('b1','hello'),('b12','good')])
    {0: 'hello', 11: 'good'}

    """
    blank_param_regex = re.compile(r'b(\d+)')
    answer = {}
    for k,v in items:
        result = blank_param_regex.match(k)
        if result:
            answer[int(result.group(1))-1] = v

    if file_items:
        file_items = list(file_items)
    if file_items and len(file_items) <= 20:
        file_items.sort()
        file_content = []
        for k,v in file_items:
            if v.size <= 100000:
                file_content.append(v.read().decode('utf-8'))
        answer[0] = ''.join(file_content)
    return answer


@login_required
def submit(request, sec_id, labinsec_id, assignment_id):
    labinsec = get_object_or_404(LabInSection, pk=labinsec_id)
    da_submission_allowed = labinsec.direct_to_lab_submission_allowed(request)
    if labinsec.disabled and not da_submission_allowed:
        return error_page(request, MSG_LAB_CLOSED)
    if labinsec.read_only and not da_submission_allowed:
        return error_page(request, MSG_READONLY)
    if not labinsec.passes_address_acl(request):
        return error_page(request, MSG_ACL)
    if not labinsec.passes_direct_to_lab(request):
        return error_page(request, MSG_DIRECT_TO_LAB_REQUIRED)

    sec = get_object_or_404(Section, pk=sec_id)
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    assignment.make_task_concrete_for_user(request.user,sec)
    task = assignment.task
    answer = build_answer(request.POST.items(),request.FILES.items())
    remote_addr = get_remote_addr_from_request(request)

    if not sec.has_student(request.user):
        return error_page(request, MSG_NOT_ENROLLED)

    submission = Submission(assignment=assignment,
                            section=sec,
                            user=request.user,
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
        submission.graded_at = datetime.datetime.now()

    submission.save()

    Log.create("submit", request,
               comment=("id: %d, task-id: %d, sect-id: %s" % 
                        (submission.id,task.id,sec_id)))

    return redirect("lab:show-assignment",
            sec_id=sec_id,
            labinsec_id=labinsec.id,
            cur_assignment_id=assignment.id)


###############################
#  AJAX view functions
###############################

@ajax_login_required
def get_assignment(request, sec_id, labinsec_id, assignment_id):
    """
    Returns html contents for current assignment for the assignment
    page for a lab.

    This ajax request is not used on MSIE as there's some jquery-ui
    tabs rendering problem.  By unknown reason, IE also requests for
    the entire page and that makes ui-tabs fail to work.

    """
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    sec = get_object_or_404(Section, pk=sec_id)
    if not sec.has_student(request.user):
        return error_page(request, MSG_NOT_ENROLLED)

    labinsec = get_object_or_404(LabInSection, pk=labinsec_id)
    da_submission_allowed = labinsec.direct_to_lab_submission_allowed(request)
    if labinsec.disabled and not da_submission_allowed:
        return error_page(request, MSG_LAB_CLOSED)
    if not labinsec.passes_address_acl(request):
        return error_page(request, MSG_ACL)
    if not labinsec.passes_direct_to_lab(request):
        return error_page(request, MSG_DIRECT_TO_LAB_REQUIRED)

    user = request.user
    assignment.make_task_concrete_for_user(user,sec)
    recent_submission = assignment.get_recent_submission_for_user(user,sec) 
    if recent_submission is not None and settings.LOG_SUBMISSION_ACCESS:
        Log.create("access", request,
                comment=("id: %d, task-id: %d, sect-id: %s" % (
                    recent_submission.id,
                    recent_submission.assignment.task_id,
                    recent_submission.section.id)))
    return render(request, 'lab/include/assignment.html',
            {
                'assignment': assignment,
                'labinsec': labinsec,
                'sec': sec,
                'recent_submission': recent_submission,
                'da_submission_allowed': da_submission_allowed,
                'is_instructor': sec.has_instructor(user),
            })


@ajax_login_required
def get_all_submissions(request, sec_id, assignment_id):
    """
    Returns html contents for 'All' tabs, called from jquery-ui tabs
    on assignment page of a lab.  Shows only the most recent
    submission.

    """
    user = request.user
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    sec = get_object_or_404(Section, pk=sec_id)
    if not sec.has_student(request.user):
        return error_page(request, MSG_NOT_ENROLLED)

    submissions = assignment.get_submissions_for_user(user,sec) 
    if len(submissions)!=0:
        cur_submission = submissions[0]
        if settings.LOG_SUBMISSION_ACCESS:
            Log.create("access", request,
                       comment=("id: %d, task-id: %d, sect-id: %s" % (
                           cur_submission.id,
                           cur_submission.assignment.task_id,
                           cur_submission.section.id)))

    else:
        cur_submission = None

    return render(request, 'lab/include/all_submissions.html',
            {
                'lab' : assignment.lab,
                'sec' : sec,
                'assignment' : assignment,
                'cur_submission' : cur_submission,
                'cur_manual_scores_json' : json.dumps(cur_submission.manual_scores),
                'submissions' : submissions 
            })


@ajax_login_required
def get_submission(request, sec_id, 
                   assignment_id, cur_submission_id):
    """
    Return html contents for showing a certian submission on the 'All'
    submission tab.

    """
    user = request.user
    submission = get_object_or_404(Submission, pk=cur_submission_id)
    if submission.user!=user:
        return error_page(request, MSG_NOT_OWNER)

    submission.make_task_concrete()

    if settings.LOG_SUBMISSION_ACCESS:
        Log.create("access", request,
                   comment=("id: %d, task-id: %d, sect-id: %s" % (
                       submission.id,
                       submission.assignment.task_id,
                       submission.section.id)))

    submission_html = template.loader.render_to_string(
        'lab/include/submission_with_copy.html',
        { 'submission': submission },
        request)

    return JsonResponse({
        'html' : submission_html,
        'manual_scores' : submission.manual_scores,
        })


def build_items_from_answer(answer):
    """
    >>> build_items_from_answer({0: 'a', 1:'abc', 2:'hello'})
    [{'name': 'b1', 'value': 'a'}, {'name': 'b2', 'value': 'abc'}, {'name': 'b3', 'value': 'hello'}]

    """
    items = []
    for k in answer.keys():
        items.append( { 'name': ("b%d" % (k+1)),
                        'value': answer[k] })
    return items


@ajax_login_required
def copy_submission(request, submission_id):
    """
    Returns json content for blanks in the current assignment taken
    from previous submissions.

    """
    user = request.user
    submission = get_object_or_404(Submission, pk=submission_id)
    if submission.user!=user:
        return error_page(request, MSG_NOT_OWNER)
    
    submission.make_task_concrete()
    items = build_items_from_answer(submission.answer)

    return JsonResponse(items,safe=False)


@ajax_login_required
def get_submission_status(request, submission_id):
    """
    Returns grading result as json that consists of a flag telling if
    the submission has be graded together with html contents on
    recent-submission-status div, the recent submission div, and the
    icon on the lab's assignment list.

    """
    user = request.user
    submission = get_object_or_404(Submission, pk=submission_id)
    if submission.user!=user:
        return error_page(request, MSG_NOT_OWNER)
    if not submission.graded():
        return JsonResponse({'graded': False}) 

    submission.make_task_concrete()

    assignment_status_html = template.loader.render_to_string(
        'lab/include/recent_submission_status_short.html',
        { 'recent_submission': submission },
        request)

    submission_html = template.loader.render_to_string(
        'lab/include/submission_with_copy.html',
        { 'submission': submission },
        request)

    submission_icon_html = template.loader.render_to_string(
        'lab/include/submission_status_icon.html',
        { 'submission': submission },
        request)

    return JsonResponse({
        'graded': True,
        'assignment_status': assignment_status_html,
        'submission': submission_html,
        'icon': submission_icon_html,
        'manual_scores': submission.manual_scores,
        })

@ajax_login_required
def explain_submission_results(request, submission_id):
    """
    Returns explanation of grading results such as grading code and testcase
    hints.

    """
    submission = get_object_or_404(Submission, pk=submission_id)

    # make sure the user owns this submission if the user is a student
    if (not request.user.is_staff) and submission.user != request.user:
        return error_page(request, MSG_NOT_OWNER)

    submission.make_task_concrete()

    testcases = submission.assignment.task.testcases
    results = zip(testcases,submission.results)
    return render(request, 'lab/include/explained_results.html', {
            'submission' : submission,
            'results' : results,
        })
