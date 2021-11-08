from django.template import Library
from django.conf import settings
from django.utils.safestring import mark_safe

register = Library()

@register.simple_tag
def mathjax():
    tag = mark_safe(
            '<script type="text/javascript" '
            'async src="{}/MathJax.js?config={}">'
            '</script>'.format(
                settings.MATHJAX_ROOT_URL,
                settings.MATHJAX_CONFIG)
            )
    return tag
