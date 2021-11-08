from django.urls import path
from . import views

app_name = 'instr'

urlpatterns = [
    path('<int:sec_id>/',
        views.section_menu,
        name='section-menu'),
    path('assignments/<int:sec_id>/',
        views.list_assignments,
        name='list-assignments'),
    path('view/<int:sec_id>/<int:assign_id>/',
        views.view_submissions,
        name='view-submissions'),
    path('submissions/<int:sec_id>/<int:student_id>/<int:assign_id>',
        views.view_assignment_submissions,
        name='view-assignment-submissions'),
    path('regrade/<int:sec_id>/<int:submission_id>/',
        views.regrade_submission,
        name='regrade-submission'),
    path('delete/<int:sec_id>/<int:submission_id>/',
        views.delete_submission,
        name='delete-submission'),
    path('regradeall/<int:sec_id>/<int:assign_id>/',
        views.regrade_submissions,
        name='regrade-submissions'),
    path('zip/<int:sec_id>/code<int:assign_id>.zip',
        views.zip_submissions,
        name='zip-submissions'),
    path('zip/<int:sec_id>/text<int:assign_id>.zip',
        views.zip_text_submissions,
        name='zip-text-submissions'),
    path('gradebook/<int:sec_id>/',
        views.gradebook,
        name='gradebook'),
    path('gradebook/csv/<int:sec_id>/',
        views.gradebook_csv,
        name='gradebook-csv'),
    path('labs/<int:sec_id>/',
        views.list_labs,
        name='list-labs'),
    path('lab/<int:labinsec_id>/report/',
        views.report_lab_status,
        name='lab-status-report'),
    path('labs/<int:sec_id>/options',
        views.show_lab_options,
        name='lab-options'),
    path('lab/<int:labinsec_id>/acl',
        views.edit_acl,
        name='edit-acl'),
    path('lab/<int:sec_id>/<int:labinsec_id>/direct-accounts',
        views.manage_direct_accounts,
        name='manage-direct-accounts'),
    path('lab/<int:sec_id>/<int:labinsec_id>/direct-accounts/remove/<int:user_id>',
        views.remove_direct_account,
        name='remove-direct-account'),
    path('lab/<int:sec_id>/<int:labinsec_id>/direct-accounts/generate/<int:user_id>',
        views.generate_direct_account,
        name='generate-direct-account'),
    path('lab/<int:sec_id>/<int:labinsec_id>/direct-accounts/action',
        views.direct_accounts_action,
        name='direct-accounts-action'),
    path('lab/<int:sec_id>/<int:labinsec_id>/direct-accounts/export',
        views.export_direct_accounts,
        name='export-direct-accounts'),
    path('logs/<int:sec_id>',
        views.report_section_log,
        name='log-report'),

    # ajax request
    path('grade/<int:submission_id>/',
        views.grade_submission,
        name='grade-submission'),
    path('lab/status/<int:lab_id>/',
        views.lab_status,
        name='lab-status'),
]