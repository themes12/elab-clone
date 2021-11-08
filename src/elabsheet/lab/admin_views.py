import re
import codecs

from django.shortcuts import get_object_or_404, render
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse, get_script_prefix
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.contrib import admin

from .models import Section, LabInSection, Announcement
from commons.utils import staff_check, username_from_student_id

##############################################################
# Enrollment views
#
@login_required
@user_passes_test(staff_check)
def list_enroll_students(request, section_id):
    section = get_object_or_404(Section, pk=section_id)
    students = section.students.all()
    return render(request, "admin/lab/section/enrollment.html",
            {
                'title' : "Student enrollment",
                'root_path' : get_script_prefix() + 'admin/',
                'section' : section,
                'students' : students,
            })

def is_possible_id(str):
    if re.match(r'^([1-9]\d{7}|[1-9]\d{9})$',str):
        return True
    if re.match(r'^[a-zA-Z][a-zA-Z0-9]*$',str):
        return True
    return False

def is_alpha_num(str):
    return re.match(r'^[a-zA-Z0-9]+$',str)!=None

def contains_num(str):
    return any(x.isdigit() for x in str)

def extract_student_info(line):
    """
    Extracts student info from string in this format: 
    [id], [firstname] [lastname]
    
    >>> extract_student_info("36052850, John Goodman")
    ['36052850', 'John', 'Goodman']
    >>> extract_student_info("36052850,John Niceman")
    ['36052850', 'John', 'Niceman']
    >>> extract_student_info("36052850 John Niceman")
    ['36052850', 'John', 'Niceman']
    >>> extract_student_info("36052850   John  Goodman")
    ['36052850', 'John', 'Goodman']
    >>> extract_student_info('"36052850", "John  Goodman"')
    ['36052850', 'John', 'Goodman']
    >>> extract_student_info('1,"36052850", "John  Goodman"')
    ['36052850', 'John', 'Goodman']
    >>> extract_student_info('1,01204111,"36052850", "John  Goodman"')
    ['36052850', 'John', 'Goodman']
    """

    # take out all '"'
    line = line.replace('"','')
    line = line.replace(',',' ')
    line = line.replace(';',' ')

    items = line.split()
    while len(items)!=0 and (not is_possible_id(items[0])):
        items = items[1:]

    if len(items)>3 and is_alpha_num(items[-1]):
        items = items[:-1]

    return items

def extract_last_name(items):
    last_name = []
    for s in items:
        s = s.strip()
        # last name should not contain a digit
        if any(x.isdigit() for x in s):
            break
        # last name should not contain a single English letter
        if len(s) == 1 and (s.isupper() or s.islower()):
            break
        last_name.append(s)
    return ' '.join(last_name)

def convert_username(student_id):
    """
    Checks if student_id matches the student ID format; if that's the
    case return the converted username, otherwise, return the original
    id.
    """
    if re.match(r'^\d+$',student_id):
        # if student id is entered, convert it to bXXXXXXX
        return username_from_student_id(student_id)
    else:
        return student_id        

def create_new_student_user(student_id, first_name, last_name):
    username = convert_username(student_id)
    try:
        user = User.objects.get(username=username)
        if first_name and last_name:
            user.first_name = first_name
            user.last_name = last_name
            user.save()
    except User.DoesNotExist:
        user = User(username=username,
                    first_name=first_name,
                    last_name=last_name)
        user.is_staff = False
        user.is_superuser = False
        user.save()

    return user

@login_required
@user_passes_test(staff_check)
def enroll_one_student(request, section_id):
    section = get_object_or_404(Section, pk=section_id)
    std_info = request.POST.get('student')
    items = extract_student_info(std_info)
    if len(items)>=3:
        std_id, first_name = items[:2]
        last_name = extract_last_name(items[2:])
        user = create_new_student_user(std_id, first_name, last_name)
        section.students.add(user)
    elif len(items)==1:
        # only have student id
        std_id = items[0]
        username = convert_username(std_id)
        try:
            # add user to this section if she is already a user
            user = User.objects.get(username=username)
            section.students.add(user)
        except:
            # no user
            pass
    return HttpResponseRedirect(reverse("lab:admin-lab-section-enrollment",
                                        args=[section.id]))

class UploadedForm(forms.Form):
    uploaded_file = forms.FileField()

@login_required
@user_passes_test(staff_check)
def upload_student_list(request, section_id):
    section = get_object_or_404(Section, pk=section_id)
    form = UploadedForm(request.POST, request.FILES)
    if form.is_valid():
        line_str = form.cleaned_data['uploaded_file'].read().splitlines()
        try:
            lines = [line.lstrip(codecs.BOM_UTF8).decode()
                     for line in line_str]
        except UnicodeError:
            try: 
                tisdecoder = codecs.getdecoder('tis-620')
                lines = [tisdecoder(line)[0] for line in line_str]
            except UnicodeDecodeError:
                return render(request, "error.html",
                        {
                            'message' :
                                'Unable to decode student list. '
                                'Please make sure the uploaded file is UTF8-encoded.',
                        })
        for line in lines:
            items = extract_student_info(line)
            if len(items)>=3:
                std_id, first_name = items[:2]
                last_name = extract_last_name(items[2:])
                user = create_new_student_user(std_id, first_name, last_name)
                section.students.add(user)
        return HttpResponseRedirect(reverse("lab:admin-lab-section-enrollment",
                                            args=[section.id]))
    else:
        # TODO: there should be some error messages
        return HttpResponseRedirect(reverse("lab:admin-lab-section-enrollment",
                                            args=[section.id]))

@login_required
@user_passes_test(staff_check)
def unenroll_students(request, section_id):
    section = get_object_or_404(Section, pk=section_id)
    student_ids = request.POST.getlist('students')
    for student_id in student_ids:
        student = User.objects.get(pk=student_id)
        section.students.remove(student)
    return HttpResponseRedirect(reverse("lab:admin-lab-section-enrollment",
                                        args=[section.id]))
    
    
##############################################################
# Section's lab set views
#

class LabNumberForm(forms.Form):
    number = forms.CharField()
    disabled = forms.BooleanField(required=False)
    read_only = forms.BooleanField(required=False)

class LabSelectionForm(forms.Form):
    selected = forms.BooleanField(required=False)

class LabInSectionForm(forms.ModelForm):
    class Meta:
        model = LabInSection
        fields = ['number', 'lab']
        widgets = {
                'lab': admin.widgets.AutocompleteSelect(
                    LabInSection._meta.get_field('lab').remote_field,
                    admin.site),
                }

@login_required
@user_passes_test(staff_check)
def list_labs_in_section(request, section_id,
                         old_cur_lab_formset=None,
                         old_avail_lab_formset=None,
                         old_other_lab_form=None):
    section = get_object_or_404(Section, pk=section_id)

    # current labs
    labs_insection = section.labinsection_set.all()
    LabNumberFormSet = formset_factory(LabNumberForm, can_delete=True, extra=0)
    form_initial = [{'number': ls.number, 'disabled': ls.disabled, 'read_only': ls.read_only} for ls in labs_insection]
    cur_lab_formset = old_cur_lab_formset or LabNumberFormSet(initial=form_initial)

    cur_lab_forms_with_labs = zip(cur_lab_formset.forms,labs_insection)

    # available labs
    avail_labs_incourse = section.get_available_labs_in_course()
    LabSelectionFormSet = formset_factory(LabSelectionForm, can_delete=True, extra=0)
    sel_form_initial = [False for lc in avail_labs_incourse]
    avail_lab_formset = old_avail_lab_formset or LabSelectionFormSet(initial=sel_form_initial)

    avail_lab_forms_with_data = zip(avail_lab_formset.forms,
                                 [ lc for lc in avail_labs_incourse ])

    other_lab_form = old_other_lab_form or LabInSectionForm()

    return render(request, "admin/lab/section/labs.html",
            {
                'title': "Section: %s" % section,
                'root_path': get_script_prefix() + 'admin/',
                'section': section,
                'cur_lab_formset': cur_lab_formset,
                'cur_lab_forms_with_labs': cur_lab_forms_with_labs,
                'avail_lab_formset': avail_lab_formset,
                'avail_lab_forms_with_data': avail_lab_forms_with_data,
                'other_lab_form': other_lab_form,
                'media': other_lab_form.media,
            })


@login_required
@user_passes_test(staff_check)
def update_labs_in_section(request, section_id):
    section = get_object_or_404(Section, pk=section_id)
    labs_insection = section.labinsection_set.all()

    LabNumberFormSet = formset_factory(LabNumberForm, can_delete=True, extra=0)
    cur_lab_formset = LabNumberFormSet(request.POST)
    if cur_lab_formset.is_valid():
        for form, lab_insection in zip(cur_lab_formset.forms, labs_insection):
            if not form.is_valid():
                return list_labs_in_section(request, section_id,
                                            old_cur_lab_formset=cur_lab_formset)
            if form.cleaned_data['DELETE']:
                lab_insection.delete()
            else:
                lab_insection.number = form.cleaned_data['number']
                lab_insection.disabled = form.cleaned_data['disabled']
                lab_insection.read_only = form.cleaned_data['read_only']
                lab_insection.save()
        return HttpResponseRedirect(reverse("lab:admin-lab-section-labs",
                                            args=[section.id]))
    else:
        return list_labs_in_section(request, section_id,
                                    old_cur_lab_formset=cur_lab_formset)

@login_required
@user_passes_test(staff_check)
def add_labs_in_section(request, section_id):
    section = get_object_or_404(Section, pk=section_id)

    avail_labs_incourse = section.get_available_labs_in_course()
    LabSelectionFormSet = formset_factory(LabSelectionForm, can_delete=True, extra=0)
    labsel_formset = LabSelectionFormSet(request.POST)

    if labsel_formset.is_valid():
        for form, avail_lab_incourse in zip(labsel_formset.forms, avail_labs_incourse):
            if not form.is_valid():
                break
            if form.cleaned_data['selected']:
                lab_insection = LabInSection(section=section,
                                             lab=avail_lab_incourse.lab,
                                             number=avail_lab_incourse.number)
                lab_insection.save()
    #else:
    #    print(labsel_formset.errors)
    return HttpResponseRedirect(reverse("lab:admin-lab-section-labs",
                                        args=[section.id]))

@login_required
@user_passes_test(staff_check)
def add_other_lab_in_section(request, section_id):
    section = get_object_or_404(Section, pk=section_id)

    f = LabInSectionForm(request.POST)
    if f.is_valid():
        lab_insection = f.save(commit=False)
        lab_insection.section = section
        lab_insection.save()
        return HttpResponseRedirect(reverse("lab:admin-lab-section-labs",
                                            args=[section.id]))
    else:
        return list_labs_in_section(request, section_id,
                                    old_other_lab_form=f)
        

##############################################################
# Section's announcement views
#

class AnnouncementForm(forms.ModelForm):
    body = forms.CharField(widget=forms.Textarea(attrs={'rows':2}))
    class Meta:
        model = Announcement
        exclude = ['section']

@login_required
@user_passes_test(staff_check)
def list_announcements(request, section_id):
    section = get_object_or_404(Section, pk=section_id)

    # current labs
    announcements = section.announcement_set.all()
    AnnouncementFormSet = modelformset_factory(Announcement, 
                                               exclude=['section'],
                                               can_delete=True,
                                               extra=0)
    announcement_formset = AnnouncementFormSet(queryset=announcements)
    new_announcement_form = AnnouncementForm()

    return render(request, "admin/lab/section/announcements.html",
            {
                'title': "Section: %s" % section,
                'root_path': get_script_prefix() + 'admin/',
                'section': section,
                'announcement_formset': announcement_formset,
                'new_form': new_announcement_form,
            })

@login_required
@user_passes_test(staff_check)
def add_announcement(request, section_id):
    section = get_object_or_404(Section, pk=section_id)

    f = AnnouncementForm(request.POST)
    if f.is_valid():
        announcement = f.save(commit=False)
        announcement.section = section
        announcement.save()

    return HttpResponseRedirect(reverse("lab:admin-lab-section-announcements",
                                        args=[section.id]))

        
@login_required
@user_passes_test(staff_check)
def update_announcements(request, section_id):
    section = get_object_or_404(Section, pk=section_id)

    AnnouncementFormSet = modelformset_factory(Announcement, 
                                               exclude=['section'],
                                               can_delete=True,
                                               extra=0)
    f = AnnouncementFormSet(request.POST,
                            queryset=section.announcement_set.all())
    if f.is_valid():
        announcements = f.save(commit=False)
        for a in announcements:
            a.section = section
            a.save()
        for a in f.deleted_objects:
            a.delete()

    return HttpResponseRedirect(reverse("lab:admin-lab-section-announcements",
                                        args=[section.id]))

        
