# Generated by Django 2.0.5 on 2018-07-14 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('framework', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menu',
            name='levels',
            field=models.ManyToManyField(to='donations.DonationLevel'),
        ),
    ]