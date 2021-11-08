from django_bootstrap import bootstrap
bootstrap()

import sys
from django.contrib.auth.models import User
from random import randrange

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} username...")
    exit(1)

for user in sys.argv[1:]:
    try:
        u = User.objects.get(username=user)
        pw = '{:05d}'.format(randrange(99999))
        u.set_password(pw)
        u.save()
        print("{},{}".format(user,pw))
    except User.DoesNotExist:
        print("User {} not found".format(user))

