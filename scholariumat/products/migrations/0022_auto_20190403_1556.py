# Generated by Django 2.1.7 on 2019-04-03 13:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0021_auto_20190331_1405'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='purchase',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.Purchase'),
        ),
    ]