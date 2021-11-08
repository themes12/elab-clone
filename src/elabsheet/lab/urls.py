from django.urls import path
from django.views.generic import TemplateView
from . import views,admin_views

app_name = 'lab'

urlpatterns = [
    path('<int:sec_id>/',
        views.list_labs,
        name='list-labs'),
    path('<int:sec_id>/<int:labinsec_id>/',
        views.show_lab,
        name='show-lab'),
    path('<int:sec_id>/<int:labinsec_id>/<int:cur_assignment_id>/',
        views.show_lab,
        name='show-assignment'),
    path('submit/<int:sec_id>/<int:labinsec_id>/<int:assignment_id>/',
        views.submit,
        name='submit-assignment'),

    # ajax request          
    path('assignment/<int:sec_id>/<int:labinsec_id>/<int:assignment_id>/', 
        views.get_assignment,
        name='get-assignment'),
    path('submissions/<int:sec_id>/<int:assignment_id>/',
        views.get_all_submissions,
        name='get-all-submissions'),
    path('submission/<int:sec_id>/<int:assignment_id>/<int:cur_submission_id>/',
        views.get_submission,
        name='get-submission'),
    path('submission/<int:submission_id>/copy/',
        views.copy_submission,
        name='copy-submission'),
    path('submission/<int:submission_id>/status/',
        views.get_submission_status,
        name='get-submission-status'),
    path('submission/<int:submission_id>/explain/',
        views.explain_submission_results,
        name='explain-submission-results'),
]

# Admin for lab: Section management
urlpatterns += [

    # enroll students
    path('admin/section/<int:section_id>/enrollment/', 
        admin_views.list_enroll_students,
        name='admin-lab-section-enrollment'),
    path('admin/section/<int:section_id>/enrollment/add', 
        admin_views.enroll_one_student,
        name='admin-lab-section-enrollment-add'),
    path('admin/section/<int:section_id>/enrollment/upload', 
        admin_views.upload_student_list,
        name='admin-lab-section-enrollment-upload'),
    path('admin/section/<int:section_id>/enrollment/delete', 
        admin_views.unenroll_students,
        name='admin-lab-section-unenroll'),

    # lab set
    path('admin/section/<int:section_id>/labs/',
        admin_views.list_labs_in_section,
        name='admin-lab-section-labs'),
    path('admin/section/<int:section_id>/labs/update',
        admin_views.update_labs_in_section,
        name='admin-lab-section-labs-update'),
    path('admin/section/<int:section_id>/labs/add',
        admin_views.add_labs_in_section,
        name='admin-lab-section-labs-add'),
    path('admin/section/<int:section_id>/labs/addother',
        admin_views.add_other_lab_in_section,
        name='admin-lab-section-labs-addother'),

    # announcement
    path('admin/section/<int:section_id>/announcements/',
        admin_views.list_announcements,
        name='admin-lab-section-announcements'),
    path('admin/section/<int:section_id>/announcements/add',
        admin_views.add_announcement,
        name='admin-lab-section-announcements-add'),
    path('admin/section/<int:section_id>/announcements/update',
        admin_views.update_announcements,
        name='admin-lab-section-announcements-update'),
]
