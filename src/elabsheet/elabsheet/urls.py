import os
from django.contrib import admin
from django.urls import include,path
from django.conf.urls.static import static
from django.conf import settings
from lab.views import index

urlpatterns = [
    path('', index,name='index'),
    path('admin/', admin.site.urls),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('cms/', include('cms.urls')),
    path('lab/', include('lab.urls')),
    path('instr/', include('instr.urls')),
    path('feedback/', include('feedback.urls')),
    path('taskpads/', include('taskpads.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
] \
+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
+ static(settings.MATHJAX_ROOT_URL, document_root=settings.MATHJAX_ROOT_DIR)
