"""
Report total number of submissions made during the last specified number of
seconds, or 60 seconds if not specified
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
print(Submission.objects.filter(submitted_at__gte=start).count())
