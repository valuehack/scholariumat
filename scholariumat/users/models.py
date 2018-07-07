import datetime
import logging

from django.urls import reverse
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from authtools.models import AbstractEmailUser
from django_countries.fields import CountryField
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from framework.behaviours import CommentAble
from .utils import get_paypal_payment, get_globee_payment


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
        donations = self.donation_set.filter(expiration__gte=datetime.date.today()).order_by('-level__amount')
        return donations[0] if donations else None

    @property
    def level(self):
        """Returns level of HIGHEST active donation"""
        active = self.donation
        return active.level if active else None

    @property
    def expiration(self):
        """Returns expiration date of the newest donation."""
        d = self.donation_set.all().order_by('-expiration')
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

    def donate(self, amount):
        """Creates donation for amount and updates balance."""
        self.refill(amount)
        level = DonationLevel.get_level_by_amount(amount)
        if level:
            self.donation_set.create(level=level)
            logger.debug('{} donated {} and is now {}.'.format(self, amount, self.level.title))
        else:
            logger.warning('{}: Could not create donation. No level available for {}.'
                           .format(self, amount))
            return False

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

    @receiver(post_save, sender=get_user_model())
    def create_user_profile(sender, instance, created, **kwargs):
        """Automatically create a profile for every user."""
        if created:
            Profile.objects.create(user=instance)
            logger.debug('Created profile for {}'.format(instance))

    def __str__(self):
        return self.user.__str__()

    class Meta():
        verbose_name = 'Nutzerprofil'
        verbose_name_plural = 'Nutzerprofile'


class DonationLevel(TitleSlugDescriptionModel):
    amount = models.SmallIntegerField(unique=True)

    @classmethod
    def get_level_by_amount(cls, amount):
        level = cls.objects.filter(amount__lte=amount).order_by('-amount')
        return level[0] if level else None

    class Meta:
        verbose_name = 'Spendenstufe'
        verbose_name_plural = 'Spendenstufen'

    def __str__(self):
        return '{}: {}'.format(self.amount, self.title)


class PaymentMethod(TitleSlugDescriptionModel):
    def __str__(self):
        return self.title

    def get_payment(self, amount):
        if self.slug == 'paypal':
            payment = get_paypal_payment(amount)
            url = next((link.href for link in payment.links if link.rel == 'approval_url'))
            return (payment.id, url)
        elif self.slug == 'globee':
            payment = get_globee_payment(amount)
            return (payment['data']['id'], payment['data']['redirect_url'])
        elif self.slug in ['bar', 'ueberweisung']:
            url = (None, reverse('users:approve_payment'))

    class Meta:
        verbose_name = 'Zahlungsmethode'
        verbose_name_plural = 'Zahlungsmethoden'


class Donation(CommentAble, TimeStampedModel):
    """Enables user to use services according to active donation level."""
    @staticmethod
    def _default_expiration():
        return datetime.date.today() + datetime.timedelta(days=settings.DONATION_PERIOD)

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    level = models.ForeignKey(DonationLevel, on_delete=models.PROTECT)
    date = models.DateField(auto_now_add=True)
    expiration = models.DateField(default=_default_expiration.__func__)
    payment_method = models.ForeignKey(PaymentMethod, null=True, blank=True, on_delete=models.SET_NULL)
    review = models.BooleanField(default=False)

    def __str__(self):
        return '%s: %s (%s)' % (self.profile.name, self.level.title, self.date)

    class Meta:
        verbose_name = 'Unterstützung'
        verbose_name_plural = 'Unterstuetzungen'
