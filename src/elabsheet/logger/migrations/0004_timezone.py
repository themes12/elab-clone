from django.db import migrations
from django.db.models import F
from django.utils import timezone

def update_log(apps, schema_editor):
    Log = apps.get_model('logger', 'Log')

    # The following loop-based code uses too much memory
    #for log in Log.objects.all():
    #    log.created_at = timezone.make_aware(log.created_at.replace(tzinfo=None))
    #    log.save()

    # Use direct queryset update instead
    Log.objects.all().update(created_at=F('created_at')+timezone.timedelta(hours=-7))


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0003_auto_20180401_1426'),
    ]

    operations = [
        migrations.RunPython(update_log),
    ]


