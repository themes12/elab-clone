"""
Update students' names in the User model with the new ones from the specified
KU-regis file.
"""
from django_bootstrap import bootstrap
bootstrap()

import sys
import re
from django.conf import settings
from django.contrib.auth.models import User
from commons.utils import username_from_student_id

SID_RE = re.compile(r"\d{8,10}")

if len(sys.argv) != 2:
    print("Usage: %s <regis-file-in-utf8>" % sys.argv[0])
    exit(1)

fin = open(sys.argv[1])
for line in fin.readlines():
    if len(line) == 0 or line.startswith("#"):
        continue
    _,_,sid,name,_,_,_ = line.split(",")
    if SID_RE.match(sid):
        username = username_from_student_id(sid)
    else:
        username = sid
    firstname,lastname = name.split(" ",1)
    try:
        user = User.objects.get(username=username)
        user.first_name = firstname
        user.last_name = lastname
        user.save()
        print("User %s updated" % username)
    except User.DoesNotExist:
        print("User %s not found" % username)

fin.close()
