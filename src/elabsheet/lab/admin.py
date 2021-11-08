from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.safestring import mark_safe


from .models import \
        Semester, Section, LabInSection, \
        AddressAcl, SingleIpLock, DirectToLabAccount, \
        Submission

admin.site.register(Semester)

class LabInSectionInline(admin.TabularInline):
    model = LabInSection
    fields = ['number', 'lab']
    autocomplete_fields = ['lab']
    verbose_name = 'Lab in this section'
    verbose_name_plural = 'Labs in this section'
    extra = 3


class SectionAdminForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['course', 'semester', 'name', 'notes', 'instructors', 'active']

    instructors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_staff=True),
        widget=admin.widgets.FilteredSelectMultiple("staffs",False))


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    inlines = [LabInSectionInline]
    form = SectionAdminForm
    list_display = ('course', 'semester', 'name', 'notes')
    search_fields = ['course__name', 'course__number', 'name']


@admin.register(LabInSection)
class LabInSectionAdmin(admin.ModelAdmin):
    fields = ['hidden_tasks']
    list_display = [
            'lab_display',
            'course_display',
            'semester_display',
            'section_display',
            'tags_display',
            ]

    def has_add_permission(self, request, obj=None):
        return False

    def lab_display(self, instance):
        return '{} {}'.format(instance.number, instance.lab.name)
    lab_display.short_description = 'Lab'

    def course_display(self, instance):
        return instance.section.course.number
    course_display.short_description = 'Course'

    def semester_display(self, instance):
        return instance.section.semester
    semester_display.short_description = 'Semester'

    def section_display(self, instance):
        return instance.section.name
    section_display.short_description = 'Section'

    def tags_display(self, instance):
        return instance.lab.tags
    tags_display.short_description = 'Tags'


@admin.register(AddressAcl)
class AddressAclAdmin(admin.ModelAdmin):
    fields = [
        'labinsec',
        'activated',
        'allowed_list',
        'processed_allowed_list',
        'denied_list',
        'processed_denied_list',
        'default_action',
        'single_ip',
    ]
    raw_id_fields = ['labinsec']
    readonly_fields = ['processed_allowed_list', 'processed_denied_list']
    list_display = ['labinsec','default_action','activated']

    def processed_allowed_list(self, instance):
        return mark_safe("<tt>" + str(instance.get_allowed_list()) + "</tt>")

    def processed_denied_list(self, instance):
        return mark_safe("<tt>" + str(instance.get_denied_list()) + "</tt>")


@admin.register(SingleIpLock)
class SingleIpLockAdmin(admin.ModelAdmin):
    raw_id_fields = ['user','labinsec']
    list_display = ['user','labinsec','ip','last_access']


@admin.register(DirectToLabAccount)
class DirectToLabAccountAdmin(admin.ModelAdmin):
    fields = ['username','password','enabled','submission_allowed','user','labinsec']
    raw_id_fields = ['user','labinsec']
    list_display = ['labinsec','user','username','password','enabled']

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    fields = ['user_info','section_link','assignment_link','submitted_at','grading_results']
    readonly_fields = ['user_info','section_link','assignment_link','submitted_at','grading_results']
    change_form_template = 'admin/lab/submission/change_form.html'

    def has_module_permission(self, request):
        return False

    def user_info(self, obj):
        return '{} - {} {}'.format(obj.user.username, obj.user.first_name, obj.user.last_name)
    user_info.short_description = 'User'

    def section_link(self, obj):
        change_url = reverse('admin:lab_section_change', args=(obj.section.id,))
        return mark_safe('<a href="{}" target="_blank">{}</a>'.format(change_url, obj.section))
    section_link.short_description = 'Section'

    def assignment_link(self, obj):
        return mark_safe(
            '<a href="{}" target="_blank">{}</a> &rarr; <a href="{}" target="_blank">{}</a>'.format(
                reverse('admin:cms_lab_change', args=(obj.assignment.lab.id,)),
                obj.assignment.lab,
                reverse('admin:cms_task_change', args=(obj.assignment.task.id,)),
                obj.assignment.task,
            )
        )
    assignment_link.short_description = 'Assignment'

    def grading_results(self, obj):
        status = obj.status_summary()
        manual = obj.sum_manual_scores()
        manual_full = obj.assignment.task.manual_full_score()
        return mark_safe('<tt>[{}] {}/{}</tt>'.format(status['results'],manual,manual_full))
    grading_results.short_description = 'Grading Results'
