from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render

from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import model_to_dict

def staff_check(user):
    return user.is_staff

@login_required
@user_passes_test(staff_check)
def search_children(request, 
                    parent_model, child_model, join_model,
                    search_result_template, search_function=None):
    """
    """
    parent_model_name = parent_model.__name__.lower()
    child_model_name = child_model.__name__.lower()
    join_model_name = join_model.__name__.lower()

    parent_id_var = "%s_id" % (parent_model_name)
    children_var = "%ss" % child_model_name
    
    if parent_id_var in request.POST:
        parent_id = request.POST[parent_id_var]
    else:
        parent_id = ''

    tags = request.POST.get('tags')
    if search_function!=None:
        children = search_function(tags)
    else:
        children = child_model.objects.filter_by_tags(tags).all()

    current_ids = {}
    if 'current' in request.POST:
        for id in request.POST.get('current').split(','):
            try:
                current_ids[int(id)] = True
            except:
                # catch id's formatting error
                pass

    new_children = []
    for child in children:
        if not child.id in current_ids:
            new_children.append(child)

    return render(request, search_result_template,
            {
                children_var: new_children,
                parent_id_var : parent_id,
                'parent_model_name' : parent_model_name,
                'child_model_name' : child_model_name,
                'join_model_name' : join_model_name,

                # 'parent_id' added so that the template knows
                'parent_id' : parent_id,
            })


class InlineAdminFormMock(object):
    """
    InlineAdminFormMock mocks the original InlineAdminForm so that the
    same inline template works for extra inline form.
    """
    def __init__(self, form, original):
        self.form = form
        self.original = original


@login_required
@user_passes_test(staff_check)
def add_child(request, 
              parent_model, child_model, 
              join_model, join_form_mock,
              one_join_form_template):
    """
    """
    parent_model_name = parent_model.__name__.lower()
    child_model_name = child_model.__name__.lower()
    join_model_name = join_model.__name__.lower()

    child_id_var = "%s_id" % child_model_name
    parent_id_var = "%s_id" % parent_model_name

    child_id = request.POST[child_id_var]
    child = get_object_or_404(child_model,pk=child_id)

    form_id = request.POST['form_id']

    join_model_args = {'number' : '',
                       child_model_name : child}

    if parent_id_var in request.POST:
        parent_id = request.POST[parent_id_var]
        if parent_id!='':
            parent = get_object_or_404(parent_model,pk=parent_id)
            join_model_args[parent_model_name] = parent

    join_item = join_model(**join_model_args)

    form = join_form_mock(initial=model_to_dict(join_item), 
                          prefix=('%s_set-%s' % (join_model_name,form_id)))
    mock_form = InlineAdminFormMock(form, join_item)

    return render(request, one_join_form_template,
            {
                'inline_admin_form' : mock_form,
                'can_delete' : True,
            })
