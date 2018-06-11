from django.db import models

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel, TitleDescriptionModel

from users.models import Profile
from framework.behaviours import CommentAble


class Product(models.Model):
    """Class to avoid MTI: Explicit OneToOneField with all products."""

    @classmethod
    def default_product(cls):
        return cls.objects.create().id


class ProductBase(TitleSlugDescriptionModel, TimeStampedModel):
    """Abstract parent class for all product type classes."""

    product = models.OneToOneField(Product, on_delete=models.CASCADE, default=Product.default_product, editable=False)

    class Meta():
        abstract = True


class Item(TitleDescriptionModel, TimeStampedModel):
    """Purchaseable items."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.IntegerField()
    limited = models.BooleanField(default=True)
    amount = models.IntegerField(null=True, blank=True)
    shipping = models.BooleanField(default=False)
    file = models.FileField(blank=True)

    # def __str__(self):
        # return self.product.select_related().__str__()

    class Meta():
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkte'


class Purchase(TimeStampedModel, CommentAble):
    """Logs purchases."""

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.SmallIntegerField(null=True, blank=True, default=1)
    balance_before = models.SmallIntegerField(editable=False)
    shipped = models.DateField(blank=True, null=True)

    def __str__(self):
        return '%dx %s (%s)' % (self.amount, self.item.product.__str__(), self.user.__str__())

    class Meta():
        verbose_name = 'Kauf'
        verbose_name_plural = 'Käufe'
