from django.db import migrations
from cms.markdown_processor import process_markdown_source

def regenerate_code(apps, schema_editor):
    Task = apps.get_model('cms', 'Task')
    for task in Task.objects.all():
        _,code,_,_ = process_markdown_source(task.source, task.language)
        task.code = code
        task.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0002_auto_20180322_1449'),
    ]

    operations = [
        migrations.RunPython(regenerate_code),
    ]
