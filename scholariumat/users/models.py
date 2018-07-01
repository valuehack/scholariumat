import datetime
import logging

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_countries.fields import CountryField
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from framework.behaviours import CommentAble


logger = logging.getLogger(__name__)


class Profile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.SmallIntegerField(default=0)

    organization = models.CharField(max_length=30, blank=True)
    street = models.CharField(max_length=30, blank=True)
    postcode = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=30, blank=True)
    country = CountryField(blank_label='- Bitte Ihr Land auswählen -', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    @property
    def address(self):
        return '%s\n%s\n%s %s\n%s' % (self.user.get_full_name(), self.street, self.postcode, self.city,
                                      self.country.name if self.country else '')

    @property
    def donation(self):
        '''Returns HIGHEST active donation.'''
        donations = self.donation_set.filter(expiration__lte=datetime.date.today()).order_by('-level__amount')
        return donations[0] if donations else None

    @property
    def level(self):
        '''Returns level of HIGHEST active donation'''
        active = self.donation
        return active.level.id if active else None

    @property
    def expiration(self):
        '''Returns expiration date of the newest donation.'''
        d = self.donation_set.all().order_by('-expiration')
        return d[0].expiration if d else None

    @property
    def active(self):
        return bool(self.donation)

    @property
    def expiring(self):
        '''Returns True if expirations date is closer than EXPIRATION_DAYS'''
        remaining = (self.expiration - datetime.date.today()).days
        return self.active & remaining < settings.EXPIRATION_DAYS

    @property
    def lendings_active(self):
        """Returns currently active lendings (not returned)."""
        return self.lending_set.filter(shipped_isnull=False, returned__isnull=True)

    def donate(self, amount):
        '''Creates donation and updates balance appropriately.'''
        self.refill(amount)
        level = DonationLevel.objects.filter(amount__mte=amount).order_by('-amount')
        if level:
            donation = self.donation_set.create()
        else:
            logger.warning('{}: Can not create donation. No level available for {}.'
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
            return False

    def refill(self, amount):
        """Refills balance."""
        self.balance += amount
        self.save()

    @receiver(post_save, sender=get_user_model())  # TODO: Avoid signals. Proxy User instead? Check in views instead?
    def create_user_profile(sender, instance, created, **kwargs):
        """Automatically create a profile for every user."""
        if created:
            Profile.objects.create(user=instance)
            logger.debug('Created profile for {}'.format(instance.name))

    def __str__(self):
        return '%s' % (self.user.__str__())

    class Meta():
        verbose_name = 'Nutzerprofil'
        verbose_name_plural = 'Nutzerprofile'


class DonationLevel(TitleSlugDescriptionModel):
    id = models.IntegerField(primary_key=True)
    amount = models.SmallIntegerField()

    class Meta:
        verbose_name = "Spendenstufe"
        verbose_name_plural = "Spendenstufen"

    def __str__(self):
        return '%s: %s (%d)' % (self.id, self.title, self.amount)


class Donation(CommentAble, TimeStampedModel):
    @staticmethod
    def _default_expiration():
        return datetime.date.today() + datetime.timedelta(days=365)

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    level = models.ForeignKey(DonationLevel, on_delete=models.PROTECT)
    date = models.DateField(auto_now_add=True)
    expiration = models.DateField(default=_default_expiration.__func__)
    payment_method = models.CharField(blank=True, max_length=100)
    review = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.profile.refill(self.level.amount)
        super(Donation, self).save(*args, **kwargs)

    def __str__(self):
        return '%s: %s (%s)' % (self.profile.user.get_full_name(), self.level.title, self.date)

    class Meta:
        verbose_name = 'Unterstützung'
        verbose_name_plural = 'Unterstuetzungen'
