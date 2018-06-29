# Generated by Django 2.0.5 on 2018-06-27 11:57

from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='name',
        ),
        migrations.AddField(
            model_name='collection',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='description'),
        ),
        migrations.AddField(
            model_name='collection',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='title', verbose_name='slug'),
        ),
        migrations.AddField(
            model_name='collection',
            name='title',
            field=models.CharField(default='bla', max_length=255, verbose_name='title'),
            preserve_default=False,
        ),
    ]
