from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def site_prefix():
    try:
        return settings.SITE_PREFIX
    except:
        return ''
