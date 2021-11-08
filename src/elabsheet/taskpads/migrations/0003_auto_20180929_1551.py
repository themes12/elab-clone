# Generated by Django 2.0.3 on 2018-09-29 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskpads', '0002_auto_20180929_1510'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='key',
            field=models.CharField(default='??????????', max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='participant',
            name='name',
            field=models.CharField(default='??????????', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='participant',
            unique_together={('post', 'key')},
        ),
    ]
