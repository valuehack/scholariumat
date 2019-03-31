import logging
import datetime

from django.db import models
from django.conf import settings

logger = logging.getLogger(__name__)


class DonationMixin(models.Model):
    """Profile mixin for managing user donations"""
    uninterested = models.BooleanField(default=False)  # Indicated no interest in future donations.

    @property
    def donations(self):
        return self.donation_set.filter(executed=True).order_by('-date')

    @property
    def donation(self):
        """Returns HIGHEST active donation."""
        return self.donations.filter(expiration__gte=datetime.date.today()).order_by('-amount').first()

    @property
    def last_donation(self):
        return self.donation_set.filter(executed=True).order_by('-date').first()

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
