from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import Feedback
from lab.models import LabInSection
from cms.models import Task

@login_required
def process(request,task_id,labinsec_id,media_type,media_id):
    try:
        if labinsec_id == 'none':
            lab_in_sec = None
        else:
            lab_in_sec = LabInSection.objects.get(id=labinsec_id)
        task = Task.objects.get(id=task_id)
        properties = dict(
                    user=request.user,
                    task=task,
                    lab_in_sec=lab_in_sec,
                    media_id=media_id,
                    media_type=media_type,
                )
        if request.method == 'POST':
                try:
                    fb = Feedback.objects.get(**properties)
                except Feedback.DoesNotExist:
                    fb = Feedback(**properties)
                fb.comments = request.POST['comments']
                fb.rating = int(request.POST['rating'])
                fb.save()
                return JsonResponse({ 'status':'ok', })
        else:
            fb = get_object_or_404(Feedback,**properties)
            return JsonResponse({
                'comments': fb.comments,
                'rating'  : fb.rating
                })
    except Exception as e:
        return JsonResponse({
            'status':'error',
            'message':str(e),
            },status=400)
