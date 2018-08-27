# Generated by Django 2.0.7 on 2018-08-23 10:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('products', '0005_item_requested'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='requested',
        ),
        migrations.AddField(
            model_name='item',
            name='requests',
            field=models.ManyToManyField(to='users.Profile'),
        ),
    ]