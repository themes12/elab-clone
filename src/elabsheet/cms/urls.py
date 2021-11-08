from django.urls import path
from . import admin_views
import search.admin_views as search_views
from .models import Lab, Task, Assignment, Course, LabInCourse
from .admin_views import AssignmentFormMock, LabInCourseFormMock

app_name = 'cms'

# Custom admin for cms: Task, Lab, Course
urlpatterns = [
    # for downloading solution code
    path('admin/task/<int:task_id>/solution/', admin_views.get_sol, 
        name='admin-cms-task-get-sol'),
    
    # this is an ajax request from admin/cms/task/change_form.html
    path('admin/task/preview/', admin_views.preview_task,
        name='admin-cms-task-preview'),

    # for previewing task on an iframe
    path('admin/task/preview-iframe/', admin_views.preview_task_as_iframe,
        name='admin-cms-task-preview-iframe'),

    # for previewing cached child task on an iframe
    path('admin/cachedchildtask/preview-iframe/<int:parent_task_id>/<key>', admin_views.preview_childtask_as_iframe,
        name='admin-cms-childtask-preview-iframe'),

    # for creating new task version
    path('admin/task/<int:task_id>/new_version/', admin_views.new_task_version,
        name='admin-cms-task-new-version'),

    # for cloning task
    path('admin/task/<int:task_id>/clone/', admin_views.clone_task,
        name='admin-cms-task-clone'),

    # for testing task
    path('admin/task/<int:task_id>/test/', admin_views.test_task,
        name='admin-cms-task-test'),

    path('admin/task/help/', admin_views.task_syntax_help,
        name='admin-cms-task-help'),

    path('admin/lab/<int:lab_id>/clone/', admin_views.clone_lab,
        name='admin-cms-lab-clone'),

    path('admin/lab/<int:lab_id>/deepclone/', admin_views.deepclone_lab,
        name='admin-cms-lab-deep-clone'),
]

# Common search admin
urlpatterns += [
    #
    # These are for task selection in lab
    #

    # this is ajax called from search button (from admin/lab/assignment-block)
    path('admin/lab/search/', 
        search_views.search_children, {
            'parent_model': Lab, 
            'child_model': Task,
            'join_model': Assignment,
            'search_result_template': 
                'admin/cms/lab/include/task_search_result.html',
            'search_function': Task.search_by_tags
            },
        'admin-cms-lab-task-search'),
    
    # this is ajax called from add button
    path('admin/lab/addtask/', 
        search_views.add_child, {
            'parent_model': Lab, 
            'child_model': Task,
            'join_model': Assignment, 
            'join_form_mock': AssignmentFormMock,
            'one_join_form_template': 
                'admin/cms/lab/include/assignment_inline_oneform.html'
            },
        'admin-cms-lab-add-task'),


    #
    # These are for lab selection in course
    #

    # this is ajax called from search button (from admin/lab/assignment-block)
    path('admin/course/search/', 
        search_views.search_children, {
            'parent_model': Course, 
            'child_model': Lab,
            'join_model': LabInCourse,
            'search_result_template': 
                'admin/cms/course/include/lab_search_result.html',
            'search_function': Lab.search_by_tags
            },
        'admin-cms-course-lab-search'),
    
    # this is ajax called from add button
    path('admin/course/addlab/', 
        search_views.add_child, {
            'parent_model': Course, 
            'child_model': Lab,
            'join_model': LabInCourse, 
            'join_form_mock': LabInCourseFormMock,
            'one_join_form_template': 
                'admin/cms/course/include/labincourse_inline_oneform.html' 
            },
        'admin-cms-course-add-lab'),
]

