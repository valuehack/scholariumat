# Generated by Django 2.0.8 on 2018-09-25 17:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_auto_20180924_1351'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['-date'], 'verbose_name': 'Veranstaltung', 'verbose_name_plural': 'Veranstaltungen'},
        ),
    ]