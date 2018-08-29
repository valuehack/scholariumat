import logging

from django.db import models
from django.conf import settings
from django.contrib import auth

from authtools.models import AbstractEmailUser
from django_countries.fields import CountryField
from django_extensions.db.models import TimeStampedModel

from library.behaviours import LendingMixin
from products.behaviours import CartMixin, BalanceMixin
from donations.behaviours import DonationMixin


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


class Profile(CartMixin, DonationMixin, LendingMixin, BalanceMixin, TimeStampedModel):
    '''Model for all User related data that is not associated with authentification.'''

    TITLE_MALE = 'm'
    TITLE_FEMALE = 'f'
    TITLE_CHOICES = [
        (TITLE_MALE, 'Herr'),
        (TITLE_FEMALE, 'Frau')
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

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

    def __str__(self):
        return self.user.__str__()

    class Meta():
        verbose_name = 'Nutzerprofil'
        verbose_name_plural = 'Nutzerprofile'
