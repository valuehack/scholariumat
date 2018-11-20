import logging
import uuid
import requests
import datetime

from django.db import models
from django.conf import settings
from django.urls import reverse_lazy

import paypalrestsdk as paypal

from framework.behaviours import CommentAble


logger = logging.getLogger(__name__)


class DonationMixin(models.Model):
    """Profile mixin for managing user donations"""
    uninsterested = models.BooleanField(default=False)  # Indicated no interest in future donations.

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


class Payment(CommentAble):
    """Mixin that handled all payment-related actions."""
    @staticmethod
    def _get_default_id():
        return uuid.uuid4().hex.upper()

    amount = models.SmallIntegerField()
    slug = models.SlugField(max_length=100, unique=True, default=_get_default_id.__func__)
    method = models.ForeignKey('donations.PaymentMethod', on_delete=models.SET_NULL, null=True, blank=True)
    executed = models.BooleanField(default=False)
    review = models.BooleanField(default=False)  # Used for manual review of some methods
    approval_url = models.CharField(max_length=200, blank=True)  # Url for customer approval of payment
    payment_id = models.SlugField(max_length=100, null=True, blank=True, unique=True)

    @property
    def reviewed(self):
        if self.method and not self.method.local_approval:
            return True
        return self.review

    @property
    def return_url(self):
        return '{}{}'.format(settings.DEFAULT_DOMAIN, reverse_lazy('donations:approve', kwargs={'slug': self.slug}))

    @property
    def cancel_url(self):
        return '{}{}'.format(settings.DEFAULT_DOMAIN, reverse_lazy('users:profile'))

    def init(self):
        """Sets approval url. Creates payment if necessary."""
        logger.debug('Initiating payment...')
        if self.method:
            if self.method.slug == 'paypal':
                return self._create_paypal()
            elif self.method.slug == 'globee':
                return self._create_globee()

        self.approval_url = self.return_url
        self.save()
        return True

    def _create_paypal(self):
        level = self.level
        payment_settings = {
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"},
            "redirect_urls": {
                "return_url": self.return_url,
                "cancel_url": self.cancel_url},
            "transactions": [{
                "payee": {
                    "email": "info@scholarium.at",
                    "payee_display_metadata": {
                        "brand_name": "scholarium"}},
                "item_list": {
                    "items": [{
                        "name": level.title,
                        "sku": level.id,
                        "price": self.amount,
                        "currency": "EUR",
                        "quantity": 1}]},
                "amount": {
                    "total": self.amount,
                    "currency": "EUR"},
                "description": level.title}]}

        paypal.configure(settings.PAYPAL_SETTINGS)
        payment = paypal.Payment(payment_settings)

        if payment.create():
            self.payment_id = payment.id
            self.approval_url = next((link.href for link in payment.links if link.rel == 'approval_url'))
            self.save()
            logger.debug("Paypal payment {} created successfully".format(self.payment_id))
            return True
        else:
            logger.exception("Payment creation failed. Paypal returned {}".format(payment.error))

    def _create_globee(self):
        headers = {
            'Accept': 'application/json',
            'X-AUTH-KEY': settings.GLOBEE_API_KEY,
        }
        payload = {
            'total': self.amount,
            'currency': 'EUR',
            'custom_payment_id': self.slug,
            'success_url': self.return_url,
            'cancel_url': self.cancel_url,
            'customer[email]': self.profile.user.email,
            'notification_email': 'info@scholarium.at',
        }
        response = requests.post(
            'https://{}globee.com/payment-api/v1/payment-request'.format(
                'test.' if settings.GLOBEE_SANDBOX else ''), headers=headers, data=payload).json()

        if response.get('success') is True:
            self.payment_id = response['data']['id']
            self.approval_url = response['data']['redirect_url']
            self.save()
            logger.debug("Globee payment {} created successfully".format(self.payment_id))
            return True
        else:
            logger.error(f'Globee payment failed: {response}')

    def execute(self, request=None):
        """
        Takes request object returned from approval urls, containing necessary execution information.
        Executes/Checks payment and creates Donation.
        """
        if not self.executed:
            if self.method:
                if self.method.slug == 'paypal':
                    if not request:
                        logger.error("No request provided. Can't execute payment.")
                        return False
                    success = self._execute_paypal(request)
                elif self.method.slug == 'globee':
                    success = self._execute_globee()
                else:
                    success = True
            else:  # Payment to be checked manually instead
                success = True

            if success:
                logger.debug("Payment {} executed successfully".format(self.slug))
                self.executed = True
                self.save()
                self.profile.refill(self.amount)
                logger.info("{} donated {} and is now level {}".format(self.profile, self.amount, self.profile.level))
                return True

    def _execute_paypal(self, request):
        paypal.configure(settings.PAYPAL_SETTINGS)
        payment = paypal.Payment.find(self.payment_id)
        return payment.execute({"payer_id": request.GET['PayerID']})

    def _execute_globee(self):
        headers = {
            'Accept': 'application/json',
            'X-AUTH-KEY': settings.GLOBEE_API_KEY}
        payment = requests.get(
            'https://{}globee.com/payment-api/v1/payment-request/{}'.format(
                'test.' if settings.GLOBEE_SANDBOX else '', self.payment_id), headers=headers).json()
        if payment.get('success') is True:
            status = payment['data'].get('status')
            if status == 'confirmed' or status == 'paid':
                return True

    class Meta:
        abstract = True
