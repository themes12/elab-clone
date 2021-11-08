from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

def remove_staff_status(modeladmin, request, queryset):
    queryset.update(is_staff=False)
remove_staff_status.short_description = "Remove staff status"

def remove_superuser_status(modeladmin, request, queryset):
    queryset.update(is_superuser=False)
remove_superuser_status.short_description = "Remove superuser status"

class MyUserAdmin(UserAdmin):
    actions = [remove_staff_status,remove_superuser_status]

admin.site.unregister(User)
admin.site.register(User,MyUserAdmin)
