# Generated by Django 2.0.5 on 2018-07-13 16:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('donations', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.Profile'),
        ),
    ]
