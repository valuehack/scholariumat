# Generated by Django 2.0.9 on 2018-12-11 21:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0005_auto_20181211_2117'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zotattachment',
            name='item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.Item'),
        ),
    ]