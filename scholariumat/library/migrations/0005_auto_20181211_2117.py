# Generated by Django 2.0.9 on 2018-12-11 20:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0004_auto_20181210_2233'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='zotitem',
            name='scholarium',
        ),
        migrations.AddField(
            model_name='zotattachment',
            name='zotitem',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='library.ZotItem'),
        ),
        migrations.AlterField(
            model_name='zotattachment',
            name='format',
            field=models.CharField(choices=[('file', 'Datei'), ('note', 'Exzerpt')], max_length=5),
        ),
    ]
