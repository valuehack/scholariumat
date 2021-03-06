# Generated by Django 2.1.7 on 2019-04-15 10:58

from django.db import migrations, models
import django.db.models.deletion


def set_defaults(apps, schema_editor):
    Livestream = apps.get_model('events', 'Livestream')
    ContentType = apps.get_model('products', 'ContentType')
    for livestream in Livestream.objects.all().iterator():
        livestream.product = livestream.item.product
        livestream.type, created = ContentType.objects.get_or_create(title='Livestream')
        livestream.save()



class Migration(migrations.Migration):

    dependencies = [
        ('products', '0024_contenttype'),
        ('events', '0007_auto_20181120_1929'),
    ]

    operations = [
        migrations.AddField(
            model_name='livestream',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='products.Product'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='livestream',
            name='type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='products.ContentType'),
            preserve_default=False,
        ),
        migrations.RunPython(set_defaults, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='livestream',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Product'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='livestream',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='products.ContentType'),
            preserve_default=False,
        ),
    ]