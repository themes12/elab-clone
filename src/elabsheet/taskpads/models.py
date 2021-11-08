from django.db import models

from django.contrib.auth.models import User
from django.db import IntegrityError

from .utils import make_result_explanation
from cms.models import Task, Assignment
from lab.models import Submission

def random_key():
    import string
    import random

    return ''.join([random.choice(string.ascii_lowercase +
                                  string.digits)
                    for _ in range(10)])
            

class TaskPad(models.Model):
    task = models.ForeignKey(Task,
                             blank=True,
                             null=True,
                             on_delete=models.CASCADE)
    creator = models.ForeignKey(User,
                                blank=True,
                                null=True,
                                on_delete=models.SET_NULL)
    
    access_key = models.CharField(max_length=30,
                                  unique=True)
    secret_key = models.CharField(max_length=30)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()

    def __str__(self):
        if self.task != None:
            return self.task.name
        else:
            return 'No task'

    def generate_random_keys(self):
        self.access_key = random_key()
        self.secret_key = random_key()

    def get_share_key(self):
        return self.secret_key[:4]
        
    @staticmethod
    def create_for(creator):
        from django.utils import timezone
        
        task_pad = TaskPad(creator=creator)
        task_pad.updated_at = timezone.now()

        tries = 0
        while tries <= 5:
            task_pad.generate_random_keys()
            try:
                task_pad.save()
                return task_pad
            except:
                pass
            tries += 1

        return None

    @staticmethod
    def clone(task_pad, creator, note=''):
        new_task_pad = TaskPad.create_for(creator)
        if not new_task_pad:
            return None
        if task_pad.task != None:
            task = task_pad.task
            new_task = Task(name=task.name,
                            language=task.language,
                            source=task.source)
            new_task.note = note
            new_task.save()

            new_task_pad.task = new_task
            new_task_pad.save()
        return new_task_pad
    
    def get_assignment(self):
        '''Return dummy assignment container for the task'''
        assignment,_ = Assignment.objects.get_or_create(
                task=self.task, lab=None, defaults={'number':''})
        return assignment


class TaskPost(models.Model):
    task_pad = models.ForeignKey(TaskPad,
                                 on_delete=models.CASCADE,
                                 related_name='task_posts')
    key = models.CharField(max_length=30,unique=True)
    participants = models.TextField(
            blank=True,
            null=True,
            help_text="Names of participants, one on each line."
                      "Empty lines and lines starting with # will be ignored.")
    enabled = models.BooleanField(default=True)
    creator = models.ForeignKey(User,
                                blank=True,
                                null=True,
                                on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self,force_insert=False,force_update=False):
        super().save(force_insert,force_update)
        if self.participants:
            self.process_participants()

    def process_participants(self):
        participant_ids = set()
        for entry in self.participants.split("\n"):
            entry = entry.strip()
            if not entry or entry.startswith('#'):
                continue
            entry = entry.replace('\t','    ')
            p = Participant.get_or_create_for(self,entry,len(participant_ids)+1)
            participant_ids.add(p.id)

        # get rid of unused participants previously created
        self.participant_set.exclude(id__in=participant_ids).delete()

    @staticmethod
    def create_for(task_pad,creator):
        post = TaskPost(task_pad=task_pad,
                        creator=creator)
        while True:
            post.key = random_key()
            try:
                post.save()
                break
            except IntegrityError:
                pass
        return post


class Participant(models.Model):
    user = models.ForeignKey(User,
            blank=True,
            null=True,
            on_delete=models.SET_NULL)
    name = models.CharField(max_length=100)
    post = models.ForeignKey(TaskPost,
            on_delete=models.CASCADE)
    key = models.CharField(max_length=30)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = (
                ('post','key'),
                ('post','name'),
                )
        ordering = ['order']

    def __str__(self):
        return '{}:{}'.format(self.order,self.name)

    @staticmethod
    def make_hash(post,name):
        '''
        Make a hash code to be used as a dummy username for a participant in a post
        '''
        import hashlib

        return 'taskpad:{}:{}'.format(
                post.key,
                hashlib.md5(name.encode('utf8')).hexdigest())

    @staticmethod
    def get_or_create_for(post,name,order):
        name = name[:100]  # truncate name if too long
        try:
            p = Participant.objects.get(post=post,name=name)
            p.order = order
            p.save()
            return p
        except Participant.DoesNotExist:
            username = Participant.make_hash(post,name)
            user,_ = User.objects.get_or_create(username=username)
            participant = Participant(
                    user=user,
                    name=name,
                    post=post,
                    order=order,
                    )
            while True:
                participant.key = random_key()
                try:
                    participant.save()
                    break
                except IntegrityError:
                    pass
            return participant


    def latest_submission_status(self):
            submission = (Submission.objects
                    .filter(assignment=self.post.task_pad.get_assignment(),
                            section=None,
                            user=self.user)
                    .order_by('-id')
                    .first())
            if submission is not None:
                status = submission.status_summary()
                status["result_explanation"] = make_result_explanation(submission)
                return status
            else:
                return None
