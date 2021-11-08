from django import template

register = template.Library()

@register.inclusion_tag('commons/tags/submission_status_detailed.html', takes_context=True)
def sub_status_detailed(context,submission):
    if 'MEDIA_URL' in context:
        media_url = context['MEDIA_URL']
    else:
        media_url = ''
    return {'MEDIA_URL' : media_url,
            'submission' : submission}

@register.inclusion_tag('commons/tags/submission_status.html', takes_context=True)
def sub_status_short(context,submission):
    if 'MEDIA_URL' in context:
        media_url = context['MEDIA_URL']
    else:
        media_url = ''
    return {'MEDIA_URL' : media_url,
            'submission' : submission}

@register.inclusion_tag('commons/tags/submission_status_icon.html', takes_context=True)
def sub_status_icon(context,submission):
    if 'MEDIA_URL' in context:
        media_url = context['MEDIA_URL']
    else:
        media_url = ''
    return {'MEDIA_URL' : media_url,
            'submission' : submission}

@register.inclusion_tag('commons/tags/lab_status.html')
def lab_status(student,section,status):
    total = status['total']
    percent = 100/total if total else 100
    return {
            'student' : student,
            'total'   : total,
            'percent' : percent,
            'section' : section,
            'status'  : status,
            }

@register.inclusion_tag('commons/tags/lab_manual_status.html')
def lab_manual_status(status):
    return {'score' : status['manual_score'],
            'total' : status['manual_total']}
