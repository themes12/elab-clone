from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('media_type', 'media_id', 'user', 'task', 'comments', 'rating')
    readonly_fields = ['user', 'task', 'lab_in_sec']
