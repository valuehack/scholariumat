from django.db import models

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel, TitleDescriptionModel

from users.models import Profile
from framework.behaviours import CommentAble, PermalinkAble


class Product(models.Model):
    """Class to avoid MTI/generic relations: Explicit OneToOneField with all products."""

    @property
    def type(self):
        """Get product object"""
        for product_rel in self._meta.related_objects:
            if product_rel.one_to_one:
                type = getattr(self, product_rel.name, None)
                if type:
                    return type
        return None

    def __str__(self):
        return self.type.__str__()


class ProductBase(TitleSlugDescriptionModel, TimeStampedModel, PermalinkAble):
    """Abstract parent class for all product type classes."""

    product = models.OneToOneField(Product, on_delete=models.CASCADE, null=True, editable=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.product:
            self.product = Product.objects.create()
            self.save()
        super(ProductBase, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class ItemType(TitleDescriptionModel, TimeStampedModel):
    limited = models.BooleanField(default=True)
    shipping = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Item Typ'
        verbose_name_plural = 'Item Typen'


class Item(TimeStampedModel):
    """Purchaseable items."""

    type = models.ForeignKey(ItemType, on_delete=models.CASCADE)
    price = models.SmallIntegerField()
    amount = models.IntegerField(null=True, blank=True)
    products = models.ManyToManyField(Product, related_name='items')
    file = models.FileField(blank=True)

    def __str__(self):
        return '%s für %d Punkte' % (self.type.__str__(), self.price)

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'


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
