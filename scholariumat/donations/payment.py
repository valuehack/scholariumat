import logging
import uuid
import requests

from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site

import paypalrestsdk as paypal


logger = logging.getLogger(__name__)


# TODO: Make payment a model.
class Payment:
    def __init__(self, method):
        domain = Site.objects.get(pk=settings.SITE_ID).domain
        self.return_url = 'https://{}{}'.format(domain, reverse('donations:approve'))
        self.method = method

    def create(self, level):
        if self.method == 'paypal':
            self._create_paypal(level)
        elif self.method == 'globee':
            self._create_globee(level)
        else:  # Don't check for payment, just return approval form
            self.id = uuid.uuid4().hex.upper()
            self.approval_url = reverse('donations:approve')

    def _create_paypal(self, level):
        payment_settings = {
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"},
            "redirect_urls": {
                "return_url": '{}?paypal=success'.format(self.return_url),
                "cancel_url": '{}?paypal=cancel'.format(self.return_url)},
            "transactions": [{
                "payee": {
                    "email": "info@scholarium.at",
                    "payee_display_metadata": {
                        "brand_name": "scholarium"}},
                "item_list": {
                    "items": [{
                        "name": level.title,
                        "sku": level.id,
                        "price": level.amount,
                        "currency": "EUR",
                        "quantity": 1}]},
                "amount": {
                    "total": level.amount,
                    "currency": "EUR"},
                "description": level.title}]}

        paypal.configure(settings.PAYPAL_SETTINGS)
        payment = paypal.Payment(payment_settings)

        if payment.create():
            logger.debug("Payment {} created successfully".format(payment.id))
            self.approval_url = next((link.href for link in payment.links if link.rel == 'approval_url'))
            self.id = payment.id
        else:
            logger.exception("Payment creation failed. Paypal returned {}".format(payment.error))

    def _create_globee(self, level):
        headers = {
            'Accept': 'application/json',
            'X-AUTH-KEY': settings.GLOBEE_API_KEY,
        }
        payload = {
            'total': level.amount,
            'currency': 'EUR',
            'custom_payment_id': level.id,
            'success_url': '{}?globee=success'.format(self.return_url),
            'cancel_url': '{}?globee=cancel'.format(self.return_url),
            'notification_email': 'info@scholarium.at',
        }
        response = requests.post(
            'https://globee.com/payment-api/v1/payment-request', headers=headers, data=payload).json()

        if response.get('success') is True:
            self.id = response['data']['id']
            self.approval_url = response['data']['redirect_url']
        else:
            logger.error('Globee payment failed.')

    def execute(self, payment_id, request):
        self.id = payment_id
        if self.method == 'paypal':
            self._execute_paypal(request)
            return True
        if self.method == 'globee':
            self._execute_globee(request)
        else:  # Payment to be checked manually instead
            return True

    def _execute_paypal(self, request):
        paypal.configure(settings.PAYPAL_SETTINGS)
        payment = paypal.Payment.find(self.id)
        return payment.execute({"payer_id": request.GET['PayerID']})

    def _execute_globee(self, request):
        headers = {
            'Accept': 'application/json',
            'X-AUTH-KEY': settings.GLOBEE_API_KEY}
        payment = requests.get(
            'https://globee.com/payment-api/v1/payment-request/{}'.format(self.id), headers=headers).json()
        if payment.get('success') is True:
            status = payment['data'].get('status')
            if status == 'confirmed' or status == 'paid':
                return True
