# Generated by Django 2.0.5 on 2018-07-13 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0002_donation_profile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='payment_id',
        ),
        migrations.AddField(
            model_name='payment',
            name='slug',
            field=models.SlugField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]