# Generated by Django 2.0.8 on 2018-09-17 10:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_auto_20180907_1504'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itemtype',
            name='limited',
        ),
    ]
