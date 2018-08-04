import datetime
import logging

from django.db import models
from django.conf import settings
from django.contrib import auth

from authtools.models import AbstractEmailUser
from django_countries.fields import CountryField
from django_extensions.db.models import TimeStampedModel


logger = logging.getLogger(__name__)


class User(AbstractEmailUser):
    '''Uses AbstractEmailUser, so everything but email and login is handled by the Profile Model.'''

    def send_activation_mail(self):
        # PW reset mail won't be send when password is None
        if not self.password:
            self.set_password(User.objects.make_random_password())
            self.save()

        reset_form = auth.forms.PasswordResetForm({'email': self.email})
        if not reset_form.is_valid():
            logger.error(f'Sending activation mail to {self.email} failed: {reset_form.errors}')
        reset_form.save(
            subject_template_name='registration/user_creation_subject.txt',
            email_template_name='registration/user_creation_email.html',
            from_email=settings.DEFAULT_FROM_EMAIL)
        logger.info(f'Activation email send to {self.email}')

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

    @property
    def lendings_active(self):
        """Returns currently active lendings (not returned)."""
        return self.lending_set.filter(shipped_isnull=False, returned__isnull=True)

    @property
    def cart(self):
        return self.purchase_set(executed=False)

    def add_to_cart(self, item, amount):
        self.purchase_set.create(item=item, amount=amount)

    def clean_cart(self):
        for purchase in self.purchase_set.filter(executed=False):
            if not purchase.available:
                purchase.delete()

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
