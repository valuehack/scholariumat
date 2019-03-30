import logging

from django.db import models
from django.conf import settings
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from framework.behaviours import PermalinkAble


logger = logging.getLogger(__name__)


class ProductBase(TitleSlugDescriptionModel, TimeStampedModel, PermalinkAble):
    """Abstract parent class for all product type classes."""

    product = models.OneToOneField('products.Product', on_delete=models.CASCADE, null=True, editable=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.product:
            from .models import Product
            self.product = Product.objects.create()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # TODO: Gets ignored in bulk delete. pre_delete signal better?
        self.product.delete()
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True


class AttachmentBase(models.Model):
    """Base class to create downloadable item attachment classes."""

    type = models.ForeignKey('products.AttachmentType', on_delete=models.PROTECT)
    item = models.ForeignKey('products.Item', on_delete=models.CASCADE, null=True, blank=True)

    def get(self):
        pass

    def __str__(self):
        item_type = self.item.type.__str__()
        type = self.type.__str__()
        return f'{item_type}: {type}' if item_type != type else type

    class Meta:
        abstract = True


class BalanceMixin(models.Model):
    """Profile mixin for storing and managing user balance"""

    balance = models.SmallIntegerField('Guthaben', default=0)

    def spend(self, amount):
        """Given an amount, tries to spend from current balance."""
        new_balance = self.balance - amount
        if new_balance >= 0:
            self.balance = new_balance
            self.save()
            return True
        else:
            logger.debug('{} tried to spend {} but only owns {}'.format(self, amount, self.balance))
            return False

    def refill(self, amount):
        """Refills balance."""
        self.balance += amount
        self.save()

    class Meta:
        abstract = True


class CartMixin(models.Model):
    """Profile mixin for storing and processing items in a shopping cart"""

    @property
    def cart(self):
        return self.purchase_set.filter(executed=False).order_by('-created')\
            .select_related('item__type').select_related('item__product')

    @property
    def cart_shipping(self):
        """Returns shipping costs of cart."""
        return settings.SHIPPING if any([purchase.item.type.shipping for purchase in self.cart]) else 0

    @property
    def cart_total(self):
        """Sums prices and adds shiping costs"""
        return sum([purchase.total for purchase in self.cart]) + self.cart_shipping

    @property
    def cart_available(self):
        return all([purchase.available for purchase in self.cart])

    def clean_cart(self):
        for purchase in self.purchase_set.filter(executed=False):
            if not purchase.available:
                purchase.delete()

    def execute_cart(self):
        if self.balance >= self.cart_total:
            for purchase in self.cart:
                purchase.execute()
            return True

    @property
    def purchases(self):
        return self.purchase_set.filter(executed=True).order_by('-modified')\
            .select_related('item__type').select_related('item__product')

    @property
    def items_bought(self):
        from .models import Item
        return Item.objects.filter(purchase__in=self.purchases).distinct()

    @property
    def products_bought(self):
        from .models import Product
        return Product.objects.filter(item__in=self.items_bought).distinct()

    @property
    def orders(self):
        return self.purchases.filter(amount__isnull=False)

    @property
    def events_booked(self):
        return self.purchases.filter(item__type__slug__in=['livestream', 'teilnahme'])

    class Meta:
        abstract = True
