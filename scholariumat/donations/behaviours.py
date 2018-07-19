import logging
import uuid
import requests

from django.db import models
from django.conf import settings
from django.urls import reverse

import paypalrestsdk as paypal

from framework.behaviours import CommentAble
from . import models as donationmodels


logger = logging.getLogger(__name__)


class Payment(CommentAble):
    amount = models.SmallIntegerField()
    slug = models.SlugField(max_length=100, null=True, blank=True, unique=True)
    method = models.ForeignKey('donations.PaymentMethod', on_delete=models.SET_NULL, null=True, blank=True)
    executed = models.BooleanField(default=False)
    review = models.BooleanField(default=False)
    approval_url = models.CharField(max_length=200, blank=True)

    def init(self):
        """Creates donation and sets id and approval url."""
        if self.method:
            if self.method.slug == 'paypal':
                return self._create_paypal()
            elif self.method.slug == 'globee':
                return self._create_globee()

        self.slug = uuid.uuid4().hex.upper()
        self.approval_url = reverse('donations:approve', kwargs={'slug': self.slug})
        self.save()
        return True

    def _create_paypal(self):
        level = donationmodels.DonationLevel.get_level_by_amount(self.amount)
        payment_settings = {
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"},
            "redirect_urls": {
                "return_url": '{}?paypal=success'.format(self.method.return_url),
                "cancel_url": '{}?paypal=cancel'.format(self.method.return_url)},
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
            self.slug = payment.id
            self.approval_url = next((link.href for link in payment.links if link.rel == 'approval_url'))
            self.save()
            logger.debug("Paypal payment {} created successfully".format(self.slug))
            return True
        else:
            logger.exception("Payment creation failed. Paypal returned {}".format(payment.error))

    def _create_globee(self):
        level = donationmodels.DonationLevel.get_level_by_amount(self.amount)
        headers = {
            'Accept': 'application/json',
            'X-AUTH-KEY': settings.GLOBEE_API_KEY,
        }
        payload = {
            'total': self.amount,
            'currency': 'EUR',
            'custom_payment_id': level.id,
            'success_url': '{}?globee=success'.format(self.method.return_url),
            'cancel_url': '{}?globee=cancel'.format(self.method.return_url),
            'notification_email': 'info@scholarium.at',
        }
        response = requests.post(
            'https://globee.com/payment-api/v1/payment-request', headers=headers, data=payload).json()

        if response.get('success') is True:
            self.slug = response['data']['id']
            self.approval_url = response['data']['redirect_url']
            self.save()
            logger.debug("Globee payment {} created successfully".format(self.slug))
            return True
        else:
            logger.error('Globee payment failed.')

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
        payment = paypal.Payment.find(self.slug)
        return payment.execute({"payer_id": request.GET['PayerID']})

    def _execute_globee(self):
        headers = {
            'Accept': 'application/json',
            'X-AUTH-KEY': settings.GLOBEE_API_KEY}
        payment = requests.get(
            'https://globee.com/payment-api/v1/payment-request/{}'.format(self.slug), headers=headers).json()
        if payment.get('success') is True:
            status = payment['data'].get('status')
            if status == 'confirmed' or status == 'paid':
                return True

    class Meta:
        abstract = True
