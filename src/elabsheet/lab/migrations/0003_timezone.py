from django.db import migrations
from django.db.models import F
from django.utils import timezone

def update_announcement(apps, schema_editor):
    Announcement = apps.get_model('lab', 'Announcement')

    # The following loop-based code uses too much memory
    #for ann in Announcement.objects.all():
    #    ann.created_at = timezone.make_aware(ann.created_at.replace(tzinfo=None))
    #    ann.save()

    # Use direct queryset update instead
    Announcement.objects.all().update(created_at=F('created_at')+timezone.timedelta(hours=-7))

def update_submission(apps, schema_editor):
    Submission = apps.get_model('lab', 'Submission')

    # The following loop-based code uses too much memory
    #for sub in Submission.objects.all():
    #    sub.submitted_at = timezone.make_aware(sub.submitted_at.replace(tzinfo=None))
    #    if sub.start_grading_at is not None:
    #        sub.start_grading_at = timezone.make_aware(sub.start_grading_at.replace(tzinfo=None))
    #    if sub.graded_at is not None:
    #        sub.graded_at = timezone.make_aware(sub.graded_at.replace(tzinfo=None))
    #    sub.save()

    # Use direct queryset update instead
    Submission.objects.all().update(submitted_at=F('submitted_at')+timezone.timedelta(hours=-7))
    Submission.objects.exclude(start_grading_at__isnull=True).update(
            start_grading_at=F('start_grading_at')+timezone.timedelta(hours=-7))
    Submission.objects.exclude(graded_at__isnull=True).update(
            graded_at=F('graded_at')+timezone.timedelta(hours=-7))


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '0002_auto_20180322_1449'),
    ]

    operations = [
        migrations.RunPython(update_announcement),
        migrations.RunPython(update_submission),
    ]

