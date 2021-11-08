from django.http import HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404
from lab.models import Section
from django.conf import settings

def ajax_login_required(view_function):
    
    def decorate(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden() 
        return view_function(request, *args, **kwargs)

    return decorate


def instructor_required(view_function):
    """
    Returns a view function that checks if the request user is an
    instructor of the section provided by the section id.

    Only works for view function that provides section id as the first
    parameter (after request).

    """
    def decorate(request, sec_id, *args, **kwargs):
        section = get_object_or_404(Section, pk=sec_id)
        if not section.has_instructor(request.user):
            return HttpResponseForbidden(
                    "<b>"
                    "Access forbidden. "
                    "Only the section's instructors are allowed in this area. "
                    "</b>"
                    )
        return view_function(request, sec_id, *args, **kwargs)

    return decorate


def taskpads_required(view_function):

    def decorate(*args, **kwargs):
        if not settings.TASKPADS_ENABLED:
            raise Http404
        return view_function(*args, **kwargs)

    return decorate
