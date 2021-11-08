from django.contrib import admin
from django import forms
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.admin import widgets
from django.contrib.auth.models import User
from django.contrib.admin import SimpleListFilter

from .models import Task, Lab, Assignment, GradingSupplement, \
        ChildTask, CachedChildTask, Course, LabInCourse

from .admin_views import TaskReadOnlyInput
from .admin_views import LabReadOnlyInput


class SupplementInline(admin.TabularInline):
    model = GradingSupplement
    extra = 1


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name','language','owner','is_private','tags','note','source','generator','text_grader']
    owner = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=True))


class SuperTaskFilter(SimpleListFilter):
    title = 'task type'
    parameter_name = 'tasktype'

    def lookups(self, request, model_admin):
        return [('r','Regular'),('s','Super')]

    def queryset(self, request, queryset):
        if self.value() == 'r':
            return queryset.filter(Q(generator__isnull=True) | Q(generator__exact=''))
        if self.value() == 's':
            return queryset.exclude(generator__isnull=True).exclude(generator__exact='')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    inlines = [SupplementInline]
    ordering = ['name']
    search_fields = ['name','tags','note','owner__username']
    list_display = ('name', 'language', 'creator','owner', 'tags', 'note', 'is_supertask')
    list_editable = ('tags','note')
    list_filter = ['language', SuperTaskFilter, 'disabled']
    form = TaskForm                               
    
    def save_formset(self, request, form, formset, change):
        '''
        Resave task after supplements have been saved
        '''
        # as all supplements point back to the same task, we only need one of
        # them
        instances = formset.save()
        if len(instances)!=0:
            task = instances[0].task
            task.save()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
            obj.owner   = request.user
        obj.save()

    def lookup_allowed(self, key, value):
        if key in ('owner__username','creator__username'):
            return True
        return super(TaskAdmin, self).lookup_allowed(key, value)


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['number','task']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_delete = True
        try:
            self.submission_count = kwargs['instance'].submission_count()
            if self.submission_count > 0:
                self.can_delete = False
        except KeyError:
            self.submission_count = ''

    number = forms.CharField(max_length=10)
    task = forms.ModelChoiceField(queryset=Task.objects,
                                  widget=TaskReadOnlyInput)
    

class AssignmentInline(admin.TabularInline):
    model = Assignment
    raw_id_fields = ['task']
    extra = 0
    template = 'admin/cms/lab/include/assignment_tabular.html'
    form = AssignmentForm


@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    inlines = [AssignmentInline]
    search_fields = ['name','tags']
    list_display = ('name', 'tags')


class LabInCourseForm(forms.ModelForm):
    class Meta:
        model = LabInCourse
        fields = ['number','lab']
    number = forms.CharField(max_length=10)
    lab = forms.ModelChoiceField(queryset=Lab.objects,
                                 widget=LabReadOnlyInput)


class LabInCourseInline(admin.TabularInline):
    model = LabInCourse
    raw_id_fields = ['lab']
    extra = 0
    template = 'admin/cms/course/include/labincourse_tabular.html'
    form = LabInCourseForm


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    autocomplete_fields = ['authors']
    inlines = [LabInCourseInline]


def evaluate_cachedchildtask(modeladmin, request, queryset):
    for ct in queryset:
        ct.evaluate_testcases()
evaluate_cachedchildtask.short_description = "Evaluate testcases"

@admin.register(CachedChildTask)
class CachedChildTaskAdmin(admin.ModelAdmin):
    list_display = ('parent_task', 'key', 'testcases_evaluated')
    fields = ('parent_task','key','source','testcases_evaluated')
    readonly_fields = ('parent_task','key','testcases_evaluated')
    actions = [evaluate_cachedchildtask]

    def has_add_permission(self, request):
        return False

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'show_save' : False,
            'show_save_and_continue' : False,
            })
        return super().change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        if '_evaluate_testcases' in request.POST:
            obj.evaluate_testcases()
            messages.success(request, "Testcases (re)evaluated successfully")
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)
