from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from datetime import datetime,timedelta
import json

from django import template
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden, \
        HttpResponseRedirect, JsonResponse
from django.urls import reverse

from commons.decorators import instructor_required, ajax_login_required
from commons.utils import find_extension
from django.contrib.auth.models import User
from lab.models import Section, Submission, Assignment, LabInSection, \
        AddressAcl, DirectToLabAccount
from lab.views import get_section_statistic_for_user
from logger.models import Log

import codecs

@login_required
@instructor_required
def section_menu(request,sec_id):
    '''Displays the main menu for a section in the instructor's view.'''
    sec = get_object_or_404(Section, pk=sec_id)
    inqueue_count = Submission.count_inqueue_submissions()
    return render(request, 'instr/section_menu.html', 
            {
                'sec' : sec,
                'inqueue_count': inqueue_count,
            })


@login_required
@instructor_required
def list_assignments(request,sec_id):
    '''Lists all assignments in the chosen section.'''
    sec = get_object_or_404(Section, pk=sec_id)
    return render(request, 'instr/assignments.html', { 'sec' : sec })


@login_required
@instructor_required
def show_lab_options(request,sec_id):
    '''Displays menu for settings lab options'''
    sec = get_object_or_404(Section, pk=sec_id)
    return render(request, 'instr/lab-options.html', { 'sec' : sec })


@login_required
@instructor_required
def manage_direct_accounts(request,sec_id,labinsec_id):
    '''Displays page for managing direct-to-lab accounts'''
    labinsec = get_object_or_404(LabInSection, pk=labinsec_id)

    # XXX should we try using ORM below?
    students = User.objects.raw('''
        SELECT 
          user.id AS id,
          user.username AS username,
          filtered_da.id AS direct_id,
          filtered_da.username AS direct_user,
          filtered_da.password AS direct_passwd,
          filtered_da.enabled AS enabled,
          filtered_da.submission_allowed AS submission_allowed
        FROM
          auth_user AS user
        INNER JOIN lab_section_students AS sec
          ON (user.id = sec.user_id AND sec.section_id = %s)
        LEFT JOIN (
          SELECT * FROM lab_directtolabaccount AS da WHERE da.labinsec_id = %s
        ) AS filtered_da
          ON (user.id = filtered_da.user_id)
        ORDER BY
          user.username
    ''',[labinsec.section_id,labinsec.id])

    return render(request, 'instr/direct-accounts.html', {
        'labinsec' : labinsec,
        'sec' : labinsec.section,
        'students' : students,
        })



@login_required
@instructor_required
def remove_direct_account(request,sec_id,labinsec_id,user_id):
    da = get_object_or_404(DirectToLabAccount,user__id=user_id,labinsec__id=labinsec_id)
    da.delete()
    return redirect('instr:manage-direct-accounts',sec_id,labinsec_id)


@login_required
@instructor_required
def direct_accounts_action(request,sec_id,labinsec_id):
    if request.method == 'POST':
        labinsec = get_object_or_404(LabInSection,id=labinsec_id)
        user_ids = [int(x) for x in request.POST.getlist('da')]
        if request.POST['action'] == 'generate':
            for uid in user_ids:
                try:
                    user = User.objects.get(id=uid)
                except User.DoesNotExist:
                    continue
                DirectToLabAccount.generate(user,labinsec)
        elif request.POST['action'] == 'remove':
            DirectToLabAccount.objects.filter(
                    labinsec=labinsec,user_id__in=user_ids).delete()
        elif request.POST['action'] == 'enable':
            DirectToLabAccount.objects.filter(
                    labinsec=labinsec,user_id__in=user_ids).update(enabled=True)
        elif request.POST['action'] == 'disable':
            DirectToLabAccount.objects.filter(
                    labinsec=labinsec,user_id__in=user_ids).update(enabled=False)
    return redirect('instr:manage-direct-accounts',sec_id,labinsec_id)


@login_required
@instructor_required
def generate_direct_account(request,sec_id,labinsec_id,user_id):
    labinsec = get_object_or_404(LabInSection,id=labinsec_id)
    user = get_object_or_404(User,id=user_id)
    DirectToLabAccount.generate(user,labinsec)
    return redirect('instr:manage-direct-accounts',sec_id,labinsec_id)


@login_required
@instructor_required
def generate_all_direct_accounts(request,sec_id,labinsec_id):
    labinsec = get_object_or_404(LabInSection, pk=labinsec_id)
    for student in labinsec.section.students.all():
        DirectToLabAccount.generate(student,labinsec)
    return redirect('instr:manage-direct-accounts',sec_id,labinsec_id)


@login_required
@instructor_required
def remove_all_direct_accounts(request,sec_id,labinsec_id):
    labinsec = get_object_or_404(LabInSection, pk=labinsec_id)
    DirectToLabAccount.objects.filter(labinsec=labinsec).delete()
    return redirect('instr:manage-direct-accounts',sec_id,labinsec_id)


@login_required
@instructor_required
def export_direct_accounts(request,sec_id,labinsec_id):
    labinsec = get_object_or_404(LabInSection, pk=labinsec_id)
    da_list = DirectToLabAccount.objects.filter(labinsec=labinsec).order_by('user__username')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
            'attachment; filename=direct-accounts-{}.csv'.format(labinsec.id)
    response.write(codecs.BOM_UTF8)
    response.write('username,name,direct-account,password,enabled\n')
    for da in da_list:
        response.write('{},{} {},{},{},{}\n'.format(
            da.user.username,
            da.user.first_name,
            da.user.last_name,
            da.username,
            da.password,
            'yes' if da.enabled else 'no',
        ))
    return response


@login_required
@instructor_required
def view_submissions(request,sec_id,assign_id):
    '''Shows all students' submissions with a score box attached to each
    text-based blank.  A submission can be graded and saved.'''
    assignment = get_object_or_404(Assignment, pk=assign_id)
    task = assignment.task
    sec = get_object_or_404(Section, pk=sec_id)
    recent_submissions = [(std, assignment.get_recent_submission_for_user(std,sec))
            for std in sec.students.all()]
    json_scores = json.dumps({std.username:submission.manual_scores
        for (std,submission) in recent_submissions if submission})
    submission_list = [(std, submission)
            for (std,submission) in recent_submissions if submission]

    # sort the submission list by submission time
    submission_list.sort(
            key=lambda std_sub_scr: std_sub_scr[1].submitted_at,
            reverse=True)

    return render(request, 'instr/submissions.html', 
            { 
                'sec' : sec,
                'submissions' : submission_list,
                'assignment' : assignment,
                'task' : task,
                'json_scores' : json_scores,
            })


@login_required
@instructor_required
def regrade_submission(request,sec_id,submission_id):
    '''Triggers regrading of specified submission'''
    previous_url = request.GET['next']
    submission = get_object_or_404(Submission,pk=submission_id)
    submission.code_grading_status = Submission.CODE_STATUS_INQUEUE
    submission.save()
    return HttpResponseRedirect(previous_url)

@login_required
@instructor_required
def delete_submission(request,sec_id,submission_id):
    previous_url = request.GET['next']
    submission = get_object_or_404(Submission,pk=submission_id)
    submission.delete()
    return HttpResponseRedirect(previous_url)


@login_required
@instructor_required
def regrade_submissions(request,sec_id,assign_id):
    '''Triggers all recent submissions for this assignment to be
    regraded.'''
    assignment = get_object_or_404(Assignment, pk=assign_id)
    sec = get_object_or_404(Section, pk=sec_id)
    recent_submissions = [(std, assignment.get_recent_submission_for_user(std,sec))
            for std in sec.students.all()]
    for std, submission in recent_submissions:
        if submission!=None:
            submission.code_grading_status = Submission.CODE_STATUS_INQUEUE
            submission.save()
    return redirect("instr:list-assignments",sec_id)


@login_required
@instructor_required
def zip_submissions(request,sec_id,assign_id):
    '''Returns all student submitted source files from the given assignment in
    form of a zip file'''
    assignment = get_object_or_404(Assignment, pk=assign_id)
    task = assignment.task
    sec = get_object_or_404(Section, pk=sec_id)
    recent_submissions = [(std, assignment.get_recent_submission_for_user(std,sec))
            for std in sec.students.all()]
    submissions = filter(lambda std_sub:std_sub[1] is not None, recent_submissions)
    submissions = sorted(submissions,key=lambda s:s[1].submitted_at)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=code%s.zip' % assign_id
    zip = ZipFile(response, mode='w', compression=ZIP_DEFLATED)
    ext = find_extension(task.language)
    for std,submission in submissions:
        fname = '%s/a%s.%s' % (std.username, assign_id, ext)
        submit_time = submission.submitted_at
        zip_info = ZipInfo(str(fname))
        zip_info.external_attr = 0o644 << 16
        zip_info.date_time = (
                submit_time.year,
                submit_time.month,
                submit_time.day,
                submit_time.hour, 
                submit_time.minute, 
                submit_time.second
                )
        zip.writestr(zip_info, 
                     codecs.encode(task.code.dump(submission.answer),
                                   'utf8'))
    response.close()
    return response


@login_required
@instructor_required
def zip_text_submissions(request,sec_id,assign_id):
    '''Returns all student submitted text answers from the given assignment in
    form of a zip file'''
    assignment = get_object_or_404(Assignment, pk=assign_id)
    task = assignment.task
    sec = get_object_or_404(Section, pk=sec_id)
    recent_submissions = [(std, assignment.get_recent_submission_for_user(std,sec))
            for std in sec.students.all()]
    submissions = filter(lambda std_sub:std_sub[1] is not None, recent_submissions)
    submissions = sorted(submissions,key=lambda s:s[1].submitted_at)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=text%s.zip' % assign_id
    zip = ZipFile(response, mode='w', compression=ZIP_DEFLATED)
    for std,submission in submissions:
        fname = '%s.txt' % std.username
        submit_time = submission.submitted_at
        zip_info = ZipInfo(str(fname))
        zip_info.external_attr = 0o644 << 16
        zip_info.date_time = (
                submit_time.year,
                submit_time.month,
                submit_time.day,
                submit_time.hour, 
                submit_time.minute, 
                submit_time.second
                )
        answers = '\f'.join([submission.answer[int(blank['id'])-1]
            for blank in task.textblanks])
        zip.writestr(zip_info, codecs.encode(answers, 'utf8'))
    response.close()
    return response


@login_required
def grade_submission(request, submission_id):
    '''Handles ajax request with scores for text answers.  It then records all
    the scores and returns the total score.'''
    submission = get_object_or_404(Submission, pk=submission_id)

    if not submission.section.has_instructor(request.user):
        return HttpResponseForbidden()

    submission.make_task_concrete()

    fullscores = dict([('b%s' % x['id'], x['score']) 
            for x in submission.assignment.task.textblanks])

    sum_score = 0
    scores = {}
    error = False
    for p,v in request.POST.items():
        if p.startswith('score_'):
            if len(v.strip()) == 0: continue
            blank_id = p[6:]
            try:
                score = int(v)
                if score < 0 or score > fullscores[blank_id]:
                    error = True
                else:
                    sum_score += score
                    scores[blank_id] = score
            except ValueError:
                error = True
    submission.manual_scores = scores
    submission.save()

    grading_status_html = template.loader.render_to_string(
            "lab/include/grading-status.html",
            { 'submission' : submission })

    return JsonResponse({
        'scores' : scores,
        'grading_status_html' : grading_status_html,
        'error' : error,
        })


@login_required
@instructor_required
def gradebook(request,sec_id,csv=False):

    def asgnmt_cnt(ls):
        return ls.lab.assignment_set.count()
    def total_manual(ls): 
        return sum([a.task.manual_full_score() for a in ls.lab.assignment_set.all()])
    def summarize(submissions):
        passed = 0
        manual_score = 0
        for submission in submissions:
            if submission!=None:
                if submission.passed():
                    passed += 1
                manual_score += submission.sum_manual_scores()
        return {'passed': passed, 'manual_score': manual_score}

    sec = get_object_or_404(Section, pk=sec_id)
    students = sec.students.order_by('username').all()

    labs = [(s.number,s.lab,asgnmt_cnt(s),total_manual(s))
            for s in sec.labinsection_set.all()]

    std_stats = {}
    for student in students:
        std_stats[student.id] = []
    for lab in [l[1] for l in labs]:
        std_submissions = (sec
                           .get_recent_submissions_by_students_for_lab(lab))

        lab_submissions = {}
        for student,all_submissions in std_submissions:
            lab_submissions[student.id] = all_submissions

        # copy to std_stats
        for user_id in std_stats.keys():
            if user_id in lab_submissions:
                std_stats[user_id].append(summarize(lab_submissions[user_id]))
            else:
                std_stats[user_id].append(summarize([]))

    all_stats = [(student,
                  map(lambda x:(x['passed'],x['manual_score']), 
                      std_stats[student.id]))
                 for student in students]

    if csv:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=grades.csv'
        for std,stats in all_stats:
            response.write(std)
            response.write(',')
            response.write(','.join(['%d,%d' % x for x in stats]))
            response.write('\n')
        return response
    else:
        return render(request, 'instr/gradebook.html', 
                {
                    'sec' : sec,
                    'labs' : labs,
                    'allstats' : all_stats,
                })


@login_required
@instructor_required
def gradebook_csv(request,sec_id):
    return gradebook(request,sec_id,True)


@login_required
@instructor_required
def list_labs(request,sec_id):
    sec = get_object_or_404(Section, pk=sec_id)
    return render(request, 'instr/labstatus.html', { 'sec' : sec })


@login_required
@instructor_required
def report_section_log(request,sec_id):
    """
    returns all logs from this section starting from yesterday.
    """
    start_time = datetime.now() - timedelta(days=1)
    logs = Log.objects.filter(created_at__gte=start_time).exclude(event='access').all()
    sec = get_object_or_404(Section, pk=sec_id)
    students = sec.students.all()
    user_id_dict = {}
    for student in students:
        user_id_dict[student.id] = True
    sect_str = (u"sect-id: %s" % sec_id)

    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = (
        'attachment; filename=log.section%s' % sec_id
        )
    for log in logs:
        stlog = log.request_ip + " " + str(log)
        if (log.event=='login') and (log.user_id in user_id_dict):
            response.write(stlog + "\n")
        elif sect_str in stlog:
            response.write(stlog + "\n")
    return response


@login_required
@instructor_required
def view_assignment_submissions(request,sec_id,student_id,assign_id):
    '''Shows all submissions of the specified assignment and section from the
    specified student.'''
    section = get_object_or_404(Section,pk=sec_id)
    student = get_object_or_404(User,pk=student_id)
    assignment = get_object_or_404(Assignment,pk=assign_id)
    submissions = Submission.objects.select_related().filter(
            assignment=assignment,
            section=section,
            user=student).order_by('-submitted_at')
    for s in submissions:
        s.make_task_concrete()
    manual_scores = {s.id:s.manual_scores for s in submissions}
    return render(request, 'instr/assignment-submissions.html', 
            {
                'student': student,
                'sec': section,
                'assignment': assignment,
                'submissions': submissions,
                'manual_scores_json': json.dumps(manual_scores),
            })


@login_required
def report_lab_status(request, labinsec_id):
    lab_in_sec = get_object_or_404(LabInSection, pk=labinsec_id)
    lab = lab_in_sec.lab
    section = lab_in_sec.section

    if not section.has_instructor(request.user):
        return HttpResponseForbidden()

    students = section.students.all()
    assignment_count = lab.assignment_set.count()

    std_submissions = (section
                       .get_recent_submissions_by_students_for_lab(lab))

    lab_submissions = {}
    for student,all_submissions in std_submissions:
        lab_submissions[student.id] = all_submissions

    # copy to std_stats
    std_stats = {}
    for user_id in [student.id for student in students]:
        if user_id in lab_submissions:
            std_stats[user_id] = lab_submissions[user_id]
        else:
            std_stats[user_id] = [None]*assignment_count

    def summarize(submission):
        if submission==None:
            return (0,0,0)
        else:
            return (submission.passed(),
                    submission.partial_code_score(),
                    submission.sum_manual_scores())

    all_stats = [(student,
                  map(summarize,std_stats[student.id]))
                 for student in students]

    response = HttpResponse(content_type='text/csv')

    filename = "lab_status-%d-%d.csv" % (section.id, lab.id)

    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    # print header row
    response.write("id%s\n" % (",passed,detailed,manual_scores" * assignment_count))

    for std,stats in all_stats:
        response.write(std)
        response.write(',')
        response.write(','.join(['%d,%3.2f,%d' % x for x in stats]))
        response.write('\n')
    return response


@ajax_login_required
def lab_status(request,lab_id):
    lab_in_sec = get_object_or_404(LabInSection, pk=lab_id)
    section = lab_in_sec.section
    lab = lab_in_sec.lab

    if not section.has_instructor(request.user):
        return HttpResponseForbidden()

    students = section.students.all()
    assignments = lab.assignment_set.all()
    assignment_count = len(assignments)
    manual_total = sum([assignment.task.manual_full_score() 
                        for assignment in assignments])

    std_submissions = (section
                       .get_recent_submissions_by_students_for_lab(lab))

    lab_submissions = {}
    for student,all_submissions in std_submissions:
        lab_submissions[student.id] = all_submissions

    # copy to std_stats
    std_stats = {}
    for user_id in [student.id for student in students]:
        if user_id in lab_submissions:
            std_stats[user_id] = lab_submissions[user_id]
        else:
            std_stats[user_id] = [None]*assignments.count()

    def summarize(submissions):
        passed = set()
        failed = set()
        submitted = 0
        manual_score = 0
        for submission in submissions:
            if submission != None:
                if submission.passed():
                    passed.add(submission.assignment)
                else:
                    failed.add(submission.assignment)
                manual_score += submission.sum_manual_scores()

        results = []
        for a in assignments:
            if a in passed:
                results.append((a,'passed'))
            elif a in failed:
                results.append((a,'failed'))
            else:
                results.append((a,None))
        return {'total': assignments.count(),
                'passed': len(passed),
                'submitted': len(passed)+len(failed),
                'results': results,
                'manual_score': manual_score,
                'manual_total': manual_total }

    all_status = [(std,
                   summarize(lab_submissions[std.id]))
                  for std in section.students.all()]

    return render(request, 'instr/include/labstatus.html', 
            {
                'all_status' : all_status,
                'section' : section,
            })


@ajax_login_required
def edit_acl(request,labinsec_id):
    labinsec = get_object_or_404(LabInSection, pk=labinsec_id)
    try:
        acl = labinsec.addressacl
        return redirect('admin:lab_addressacl_change',acl.id)
    except AddressAcl.DoesNotExist:
        return redirect(reverse('admin:lab_addressacl_add') + 
                "?labinsec={}".format(labinsec.id))
