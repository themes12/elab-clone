"""
Set up the current environment for accessing django applications.  Put the following code first in a script:

    from django_bootstrap import bootstrap
    bootstrap()
"""
import os
import sys
import django

def bootstrap():
    sys.path.append(os.path.join(os.path.dirname(__file__),".."))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE","elabsheet.settings")
    django.setup()
