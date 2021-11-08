from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('<int:task_id>/<labinsec_id>/<media_type>/<media_id>/',
        views.process,
        name='process'),
]
