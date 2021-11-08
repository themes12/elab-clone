"""
Report a list of all submissions' time and grading status in the lab specified
by lab-in-sec-id.  Each output row consists of:
    * submission id
    * assignment number (i.e., task no.)
    * username
    * submission time (YYYY-MM-DD HH:MM:SS)
    * grading result (0 - failed, 1 - passed)
"""
from django_bootstrap import bootstrap
bootstrap()

import sys
from django.conf import settings
from django.utils import timezone
from lab.models import Submission,LabInSection

if len(sys.argv) != 2:
    print("Usage: %s <lab-in-sec-id>" % sys.argv[0])
    exit(1)

lis_id = int(sys.argv[1])
lis = LabInSection.objects.get(id=lis_id)

slist = Submission.objects.filter(section=lis.section,assignment__lab=lis.lab)
for s in slist:
    print("{},{},{},{},{}".format(
        s.id,
        s.assignment.number,
        s.user.username,
        timezone.localtime(s.submitted_at).strftime("%Y-%m-%d %H:%M:%S"),
        1 if s.passed() else 0)
        )
