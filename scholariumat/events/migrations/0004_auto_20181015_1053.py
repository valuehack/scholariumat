# Generated by Django 2.0.8 on 2018-10-15 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_auto_20180925_1952'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='time_end',
            new_name='_time_end',
        ),
        migrations.RenameField(
            model_name='event',
            old_name='time_start',
            new_name='_time_start',
        ),
        migrations.AddField(
            model_name='eventtype',
            name='default_time_end',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='eventtype',
            name='default_time_start',
            field=models.TimeField(blank=True, null=True),
        ),
    ]