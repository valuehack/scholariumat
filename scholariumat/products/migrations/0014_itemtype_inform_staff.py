# Generated by Django 2.0.9 on 2018-12-02 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_auto_20181125_1246'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemtype',
            name='inform_staff',
            field=models.BooleanField(default=False),
        ),
    ]