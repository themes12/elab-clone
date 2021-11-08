# Generated by Django 2.0.3 on 2018-07-29 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0011_task_text_grader'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='generator',
            field=models.TextField(blank=True, help_text='Python script defining the function <tt>generate(seed,difficulty)</tt> to generate a child task by returning a dict of variable substituions.', null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='text_grader',
            field=models.TextField(blank=True, help_text='Python script defining the function <tt>grade(index,max_score,solution,answer)</tt> to return a score for the given answer, or None if the answer is not to be graded.', null=True),
        ),
    ]
