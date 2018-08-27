import logging
import datetime

from django.db import models
from django.conf import settings


logger = logging.getLogger(__name__)


class CartMixin(models.Model):
    """Profile mixin for storing and processing items in a shopping cart"""

    @property
    def cart(self):
        return self.purchase_set.filter(executed=False)

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

    class Meta:
        abstract = True


class DonationMixin(models.Model):
    """Profile mixin for managing user donations"""

    @property
    def donations(self):
        return self.donation_set.filter(executed=True).order_by('-date')

    @property
    def donation(self):
        """Returns HIGHEST active donation."""
        donations = self.donations.filter(expiration__gte=datetime.date.today()).order_by('-amount')
        return donations[0] if donations else None

    @property
    def last_donation(self):
        donations = self.donation_set.filter(executed=True).order_by('-date')
        return donations[0] if donations else None

    @property
    def expired_donations(self):
        return self.donation_set.filter(executed=True, expiration__lt=datetime.date.today()).order_by('-date')

    @property
    def level(self):
        """Returns level of HIGHEST active donation"""
        active = self.donation
        return active.level if active else None

    @property
    def expiration(self):
        """Returns expiration date of the newest donation."""
        donation = self.last_donation
        return donation.expiration if donation else None

    @property
    def amount(self):
        """Returns amount of active donation."""
        donation = self.donation
        return donation.amount if donation else 0

    @property
    def last_amount(self):
        """Returns amount of the newest donation."""
        donation = self.last_donation
        return donation.amount if donation else None

    @property
    def active(self):
        return bool(self.donation)

    @property
    def expiring(self):
        """Returns True if expirations date is closer than EXPIRATION_DAYS"""
        remaining = (self.expiration - datetime.date.today()).days if self.expiration else False
        return self.active and remaining < settings.EXPIRATION_DAYS

    def donate(self, amount, donation_kwargs={}):
        """Creates donation for amount and refills balance."""
        donation = self.donation_set.create(amount=amount, **donation_kwargs)
        donation.execute()

    def clean_donations(self):
        for donation in self.donation_set.filter(executed=False):
            donation.delete()

    class Meta:
        abstract = True


class LendingMixin(models.Model):
    """Profile Mixin for managing item lendings"""

    @property
    def lendings_active(self):
        """Returns currently active lendings (not returned)."""
        return self.lending_set.filter(shipped_isnull=False, returned__isnull=True)

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
