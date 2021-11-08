from django.contrib.auth.models import User
from django.db import models

from cms.models import Task
from lab.models import LabInSection

class Feedback(models.Model):
    """
    Keep track of user feedbacks for media/contents embedded in a task
    """
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    task = models.ForeignKey(Task,on_delete=models.CASCADE)
    lab_in_sec = models.ForeignKey(LabInSection,null=True,on_delete=models.SET_NULL)
    media_type = models.CharField(max_length=20)
    media_id = models.CharField(max_length=64)
    comments = models.TextField(blank=True)
    rating = models.IntegerField()

    class Meta:
        index_together = [
            ('media_type','media_id'),
        ]

    def __str__(self):
        return "{}-{} by {}".format(
                self.media_type,
                self.media_id,
                self.user)
