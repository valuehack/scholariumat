# Generated by Django 2.0.9 on 2018-12-10 21:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0003_zotitem_scholarium'),
    ]

    operations = [
        migrations.AddField(
            model_name='zotitem',
            name='amount',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='zotitem',
            name='price',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='zotitem',
            name='price_digital',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='zotitem',
            name='printing',
            field=models.BooleanField(default=False),
        ),
    ]