# Generated by Django 2.0.8 on 2018-09-10 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0006_auto_20180910_1213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='time_end',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='time_start',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
