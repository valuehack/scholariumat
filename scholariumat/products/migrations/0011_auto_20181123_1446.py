# Generated by Django 2.0.9 on 2018-11-23 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_itemtype_additional_supply'),
    ]

    operations = [
        migrations.RenameField(
            model_name='itemtype',
            old_name='requestable',
            new_name='request_price',
        ),
        migrations.RemoveField(
            model_name='itemtype',
            name='unavailability_notice',
        ),
        migrations.AddField(
            model_name='itemtype',
            name='buy_unauthenticated',
            field=models.BooleanField(default=False),
        ),
    ]