# Generated by Django 2.0.3 on 2018-04-01 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logger', '0002_auto_20180322_1450'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
