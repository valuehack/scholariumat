import logging

from django.db import models
from django.conf import settings


logger = logging.getLogger(__name__)


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
        return self.purchase_set.filter(executed=False).order_by('-created')

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

    def add_to_cart(self, item, amount):
        self.purchase_set.create(item=item, amount=amount)

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
        return self.purchase_set.filter(executed=True).order_by('-modified')

    @property
    def orders(self):
        return self.purchases.filter(item__type__limited=True)

    @property
    def events_booked(self):
        return self.purchases.filter(item__type__slug__in=['livestream', 'teilnahme'])

    class Meta:
        abstract = True
