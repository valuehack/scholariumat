import datetime

from django.db import models
from django.conf import settings

from django_countries.fields import CountryField
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from framework.behaviours import CommentAble


class ContactInfo(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.CharField(max_length=30, blank=True)
    street = models.CharField(max_length=30, blank=True)
    postcode = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=30, blank=True)
    country = CountryField(blank_label='- Bitte Ihr Land auswählen -', null=True)
    phone = models.CharField(max_length=20, blank=True)

    def get_address(self):
        return '%s\n%s\n%s %s\n%s' % (self.user.get_full_name(), self.street, self.postcode, self.city,
                                      self.country.name if self.country else '')


class Profile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.SmallIntegerField(default=0)

    @property
    def donation(self):
        '''Returns HIGHEST active donation.'''
        donations = self.donation_set.all().order_by('-level__amount')
        active = [d for d in donations if d.get_expiration() >= datetime.date.today()]
        return active[0] if active else None

    @property
    def level(self):
        '''Returns level of HIGHEST active donation'''
        active = self.get_active()
        return active.stufe if active else None

    @property
    def expiration(self):
        '''Returns expiration date of the newest donation.'''
        d = self.donation_set.all().order_by('-expiration')
        return d[0] if d else None

    @property
    def status(self):
        states = [
            (0, "Kein Unterstützer"),
            (1, "Abgelaufen"),
            (2, "30 Tage bis Ablauf"),
            (3, "Aktiv")
        ]
        if self.get_expiration():
            remaining = (self.get_expiration() - datetime.date.today()).days
            if remaining < 0:
                return states[1]
            elif remaining < 30:
                return states[2]
            else:
                return states[3]
        else:
            return states[0]

    @property
    def lendings_active(self):
        return self.lending_set.filter(shipped_isnull=False, returned__isnull=True)

    def __str__(self):
        return '%s (%s)' % (self.user.get_full_name(), self.user.email)

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
        return '%s: %s (%d)' % (self.id, self.name, self.amount)


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
            self.profile += self.level.amount
            self.profile.save()
        super(Donation, self).save(*args, **kwargs)

    def __str__(self):
        return '%s: %s (%s)' % (self.profile.user.get_full_name(), self.level.name, self.date)

    class Meta:
        verbose_name = 'Unterstützung'
        verbose_name_plural = 'Unterstuetzungen'
