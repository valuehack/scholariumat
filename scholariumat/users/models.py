import datetime
import logging

from django.db import models
from django.conf import settings

from authtools.models import AbstractEmailUser
from django_countries.fields import CountryField
from django_extensions.db.models import TimeStampedModel


logger = logging.getLogger(__name__)


class User(AbstractEmailUser):
    '''Uses AbstractEmailUser, so everything but email is handled by the Profile Model.'''

    class Meta(AbstractEmailUser.Meta):
        swappable = 'AUTH_USER_MODEL'
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class Profile(TimeStampedModel):
    '''Model for all User related data that is not associated with authentification.'''
    TITLE_MALE = 'm'
    TITLE_FEMALE = 'f'
    TITLE_CHOICES = [
        (TITLE_MALE, 'Herr'),
        (TITLE_FEMALE, 'Frau')
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.SmallIntegerField('Guthaben', default=0)
    title = models.CharField('Anrede', max_length=1, choices=TITLE_CHOICES, null=True)
    name = models.CharField(max_length=200, blank=True)
    organization = models.CharField('Firma', max_length=30, blank=True)
    street = models.CharField('Straße', max_length=30, blank=True)
    postcode = models.CharField('PLZ', max_length=10, blank=True)
    city = models.CharField('Ort', max_length=30, blank=True)
    country = CountryField('Land', blank_label='- Bitte Ihr Land auswählen -', null=True, blank=True)
    phone = models.CharField('Telefonnummer', max_length=20, blank=True)

    @property
    def address(self):
        return '{}\n{}\n{} {}\n{}'.format(self.name, self.street, self.postcode,
                                          self.city, self.country.get('name', ''))

    @property
    def donation(self):
        """Returns HIGHEST active donation."""
        donations = self.donation_set.filter(executed=True, expiration__gte=datetime.date.today()).order_by('-amount')
        return donations[0] if donations else None

    @property
    def level(self):
        """Returns level of HIGHEST active donation"""
        active = self.donation
        return active.level if active else None

    @property
    def expiration(self):
        """Returns expiration date of the newest donation."""
        d = self.donation_set.filter(executed=True).order_by('-expiration')
        return d[0].expiration if d else None

    @property
    def active(self):
        return bool(self.donation)

    @property
    def expiring(self):
        """Returns True if expirations date is closer than EXPIRATION_DAYS"""
        remaining = (self.expiration - datetime.date.today()).days if self.expiration else False
        return self.active and remaining < settings.EXPIRATION_DAYS

    @property
    def lendings_active(self):
        """Returns currently active lendings (not returned)."""
        return self.lending_set.filter(shipped_isnull=False, returned__isnull=True)

    def donate(self, amount, donation_kwargs={}):
        """Creates donation for amount and refills balance."""
        donation = self.donation_set.create(amount=amount, **donation_kwargs)
        donation.execute()

    def clean_donations(self):
        for donation in self.donation_set.filter(executed=False):
            donation.delete()

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

    def __str__(self):
        return self.user.__str__()

    class Meta():
        verbose_name = 'Nutzerprofil'
        verbose_name_plural = 'Nutzerprofile'
