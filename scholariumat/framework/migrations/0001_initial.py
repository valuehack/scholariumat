# Generated by Django 2.0.5 on 2018-07-13 16:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('donations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('levels', models.ManyToManyField(to='donations.Donation')),
            ],
        ),
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('title', models.CharField(max_length=50)),
                ('target', models.CharField(max_length=50)),
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('menu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='framework.Menu')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='MenuSubItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('target', models.CharField(max_length=50)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='framework.MenuItem')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
