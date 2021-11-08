"""
Count how many submissions are currently queued for grading.
"""
from django_bootstrap import bootstrap
bootstrap()
from django.conf import settings
from lab.models import Submission

print(Submission.count_inqueue_submissions())
