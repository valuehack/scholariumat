from django.db import models

from django_extension.db.models import TimeStampedModel, TitleSlugDescriptionModel
from annoying.fields import AutoOneToOneField

from framework.models import Profile


class Product(models.Model):
    """Class to avoid MTI: Explicit OneToOneField with all products."""
    pass


class ProductBase(TitleSlugDescriptionModel, TimeStampedModel):
    """Abstract parent class for all product type classes."""

    product = AutoOneToOneField(Product, on_delete=models.CASCADE, related_name='type')

    class Meta():
        abstract = True


class Item(TimeStampedModel):
    """Purchaseable items."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.IntegerField()
    limited = models.BooleanField(default=True)
    amount = models.IntegerField(null=True, bank=True)
    shipping = models.BooleanField(default=False)
    file = models.FileField(blank=True)

    class Meta():
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkte'


class Purchase(TimeStampedModel):
    """Logs purchases."""

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.SmallIntegerField(null=True, blank=True, default=1)
    comment = models.CharField(max_length=255, blank=True)
    balance_before = models.SmallIntegerField(editable=False)
    shipped = models.DateField(blank=True, null=True)

    def __str__(self):
        return '%dx %s (%s)' % (self.amount, self.product.__str__(), self.user.__str__())

    class Meta():
        verbose_name = 'Kauf'
        verbose_name_plural = 'Käufe'
