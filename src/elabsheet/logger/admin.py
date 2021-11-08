from django.contrib import admin

from .models import Log

class LogAdmin(admin.ModelAdmin):
    search_fields = ['user__username','user__first_name','request_ip']
    list_filter = ['event']

admin.site.register(Log,LogAdmin)
