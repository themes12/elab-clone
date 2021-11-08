from django.urls import path
from . import views

app_name = 'taskpads'

urlpatterns = [
    path('',
        views.index,
        name='index'),
    path('new/',
        views.new,
        name='new'),


    path('preview/iframe/',
         views.preview_iframe,
         name='preview-iframe'),
    path('preview/',
         views.preview,
         name='preview'),

    path('test/<access_key>/<secret_key>/',
        views.test_task,
        name='test-task'),

    path('change/<access_key>/<secret_key>/',
        views.change,
        name='change'),
    path('manage/<access_key>/<secret_key>/',
        views.manage,
        name='manage'),
    path('newpost/<access_key>/<secret_key>/',
        views.create_post,
        name='newpost'),

    path('post/<post_key>/',
        views.edit_post,
        name='editpost'),

    path('show/<access_key>/',
        views.show,
        name='show'),
    path('clone/<access_key>/<share_key>/',
        views.clone,
        name='clone'),
    path('workon/<post_key>/<participant_key>/',
        views.workon,
        name='workon'),
    path('submit/<post_key>/<participant_key>/',
        views.ajax_submit,
        name='ajax_submit'),
    path('post/export/<post_key>.txt',
        views.post_export_txt,
        name='post_export_txt'),
    path('post/export/<post_key>.csv',
        views.post_export_csv,
        name='post_export_csv'),

    path('submission-status/<participant_key>/<int:submission_id>/',
        views.ajax_submission_status,
        name='ajax_submission_status'),
]
