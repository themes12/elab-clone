from django.template import Library
import markdown as md

register = Library()

@register.filter
def markdown(text):
    """
    Render the given text using Markdown

    """
    return md.markdown(text)
