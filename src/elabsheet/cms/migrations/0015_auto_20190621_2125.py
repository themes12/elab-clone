# Generated by Django 2.0.9 on 2019-06-21 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0014_auto_20181003_2021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='text_grader',
            field=models.TextField(blank=True, help_text='Python script defining the function <tt>grade(index,max_score,solution,answer)</tt> or <tt>grade(index,max_score,solution,answer,elab)</tt> to return a score for the given answer, or None if the answer is not to be graded.', null=True),
        ),
    ]
