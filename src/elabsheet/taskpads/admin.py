from django.contrib import admin
from .models import TaskPost

@admin.register(TaskPost)
class TaskPostAdmin(admin.ModelAdmin):
    list_display = ('get_task', 'task_key', 'post_key')

    def get_task(self,obj):
        return obj.task_pad.task.name
    get_task.short_description = "Task"

    def task_key(self,obj):
        return "{}/{}".format(
                obj.task_pad.access_key,
                obj.task_pad.secret_key,
                )
    task_key.short_description = "Task Key"

    def post_key(self,obj):
        return obj.key
    post_key.short_description = "Post Key"
