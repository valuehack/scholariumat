# Generated by Django 2.1.7 on 2019-03-29 12:48

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0005_auto_20181119_1707'),
        ('products', '0018_auto_20190328_1931'),
    ]

    operations = [
        migrations.CreateModel(
            name='Discount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discount', models.PositiveSmallIntegerField(validators=[django.core.validators.MaxValueValidator(100)])),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='donations.DonationLevel')),
            ],
        ),
        migrations.AddField(
            model_name='item',
            name='discounts',
            field=models.ManyToManyField(blank=True, to='products.Discount'),
        ),
    ]
