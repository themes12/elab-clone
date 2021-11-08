"""
Report a list of all submissions' time and grading status in the section specified
by section id.  Each output row consists of:
    * submission id
    * lab number
    * task number
    * username
    * submission time (YYYY-MM-DD HH:MM:SS)
    * grading result (0 - failed, 1 - passed)
"""
from django_bootstrap import bootstrap
bootstrap()

import sys
from django.conf import settings
from django.utils import timezone
from lab.models import Submission,Section,LabInSection
#from django.db import connection

if len(sys.argv) != 2:
    print("Usage: %s <sec-id>" % sys.argv[0])
    exit(1)

sec_id = int(sys.argv[1])

slist = Submission.objects.filter(section_id=sec_id).prefetch_related('user','assignment')
lis_cache = {}
for s in slist:
    sec_asmt_pair = (s.section_id,s.assignment_id)
    try:
        lis = lis_cache[sec_asmt_pair]
    except KeyError:
        lis = LabInSection.objects.get(section=s.section,lab=s.assignment.lab)
        lis_cache[sec_asmt_pair] = lis
    print("{},{},{},{},{},{}".format(
        s.id,
        lis.number,
        s.assignment.number,
        s.user.username,
        timezone.localtime(s.submitted_at).strftime("%Y-%m-%d %H:%M:%S"),
        1 if s.passed() else 0)
        )
