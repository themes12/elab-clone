from django.template import Library
from django.urls import get_script_prefix
from elabsheet.settings import SITE_NAME

register = Library()

def script_prefix():
    """
    Returns script prefix for url.  It basically returns "django.root".
    """
    return get_script_prefix()
script_prefix = register.simple_tag(script_prefix)

def site_name():
    """
    Returns the site name specified in the settings file
    """
    return SITE_NAME
site_name = register.simple_tag(site_name)

