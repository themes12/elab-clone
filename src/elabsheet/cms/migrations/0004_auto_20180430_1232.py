# Generated by Django 2.0.3 on 2018-04-30 05:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0003_regenerate_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='language',
            field=models.CharField(choices=[('python', 'python'), ('python2', 'python2'), ('python3', 'python3'), ('csharp', 'csharp'), ('java', 'java'), ('c', 'c'), ('c++', 'c++'), ('c++11', 'c++11'), ('plaintext', 'plaintext'), ('makefile', 'makefile'), ('shellscript', 'shellscript')], max_length=20),
        ),
    ]
