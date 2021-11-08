"""
Report a list of all passed submissions in the specified lab-in-sec with the
assignment number and the time the submission was made.
"""
from django_bootstrap import bootstrap
bootstrap()

import sys
from django.utils import timezone
from django.conf import settings
from lab.models import Submission,LabInSection

if len(sys.argv) != 2:
    print("Usage: %s <lab-in-sec-id>" % sys.argv[0])
    exit(1)

lis_id = int(sys.argv[1])
lis = LabInSection.objects.get(id=lis_id)

slist = Submission.objects.filter(section=lis.section,assignment__lab=lis.lab)
for s in slist:
    if s.passed():
        print("%s,%s" % (s.assignment.number,s.submitted_at))
