"""
Report average grading time during the last specified number of seconds, or
60 seconds if not specified.
"""
from django_bootstrap import bootstrap
bootstrap()

import sys
from django.conf import settings
from django.utils import timezone
from lab.models import Submission

if len(sys.argv) != 2:
    seconds = 60
else:
    seconds = int(sys.argv[1])

start = timezone.now() - timezone.timedelta(seconds=seconds)
submissions = Submission.objects.filter(submitted_at__gte=start)
gradeTimes = [(s.graded_at-s.start_grading_at).total_seconds()
        for s in submissions 
        if s.start_grading_at is not None and s.graded_at is not None]
if gradeTimes:
    print(sum(gradeTimes)/len(gradeTimes))
else:
    print(0)
