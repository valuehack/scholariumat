import logging
import uuid
import requests
import hashlib

from django.urls import reverse
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.staticfiles.templatetags.staticfiles import static

import paypalrestsdk

from .models import DonationLevel


logger = logging.getLogger(__name__)


class Payment:
    def __init__(self, amount):
        self.amount = amount
        self.id = uuid.uuid4().hex.upper()
        self.domain = Site.objects.get(pk=settings.SITE_ID).domain
        self.approval_url = reverse('users:donate')
        self.level = DonationLevel.get_level_by_amount(amount)


class PaypalPayment(Payment):
    def __init__(self, *args, **kwargs):
        super(PaypalPayment, self).__init__(*args, **kwargs)
        self.sdk = paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET})

    def create_profile(self):
        """Creates Paypal Web Profile"""
        profile_settings = {
            "presentation": {
                "brand_name": "scholarium",
                "logo_image": "https://{}{}".format(self.domain, static('img/scholarium_et.jpg')),
                "locale_code": "AT"
            },
            "input_fields": {
                "allow_note": True,
                "no_shipping": 1,
                "address_override": 1
            },
            "flow_config": {
                "landing_page_type": "login",
                "bank_txn_pending_url": 'https://{}{}'.format(self.domain, reverse('users:donate')),
                "user_action": "commit"
            }}
        # Settings-Hash as name, so we don't create already existing profiles.
        profile_name = hashlib.sha256(profile_settings).hexdigest()
        profile_settings['name'] = profile_name
        web_profile = self.sdk.WebProfile(profile_settings)
        if web_profile.create():
            logger.debug("Created Web Profile {}".format(web_profile.id))
        else:
            logger.exception("Paypal returned {}".format(web_profile.error))

    def create(self):
        payment = self.sdk.Payment({
            "intent": "sale",
            "experience_profile_id": settings.PAYPAL_WEB_PROFILE,
            "payer": {
                "payment_method": "paypal"},
            "redirect_urls": {
                "return_url": 'https://{}{}?paypal=success'.format(self.domain, reverse('users:donate')),
                "cancel_url": 'https://{}{}?paypal=cancel'.format(self.domain, reverse('users:donate'))},
            "transactions": [{
                "payee": {
                    "email": "info@scholarium.at",
                    "payee_display_metadata": {
                        "brand_name": "scholarium"}},
                "item_list": {
                    "items": [{
                        "name": self.level.title,
                        "sku": self.level.id,
                        "price": self.level.amount,
                        "currency": "EUR",
                        "quantity": 1}]},
                "amount": {
                    "total": self.amount,
                    "currency": "EUR"},
                "description": self.level.title}]})

        if payment.create():
            logger.debug("Payment[%s] created successfully" % (payment.id))
            self.approval_url = next((link.href for link in payment.links if link.rel == 'approval_url'))
            self.id = payment.id
            return True
        else:
            logger.exception("Paypal returned {}".format(payment.error))
            return False

    def execute(self, payment_id):
        if self.slug == 'paypal':
            paypalrestsdk.configure({
                "mode": settings.PAYPAL_MODE,
                "client_id": settings.PAYPAL_CLIENT_ID,
                "client_secret": settings.PAYPAL_CLIENT_SECRET})
            payment = paypalrestsdk.Payment.find(payment_id)
            if payment.execute({"payer_id": request.GET['PayerID']}):
                upgrade_mail(request.user.my_profile, stufe, zahlungsmethode='p')
                return upgrade_redirect()
            elif payment.error['name'] == 'PAYMENT_ALREADY_DONE':
                pass
            else:
                logger.error('Paypal payment failed: {}'.format(payment.error))
                messages.error(request, settings.MESSAGES_UNEXPECTED_ERROR)
        else:
            messages.error(request, 'Session abgelaufen. Bitte probieren Sie es erneut.')
            print(request.session['payment_id'], payment_id)
            return HttpResponseRedirect(reverse('gast_spende'))


class GlobeePayment(Payment):
    def create(self):
        headers = {
            'Accept': 'application/json',
            'X-AUTH-KEY': settings.GLOBEE_API_KEY,
        }
        payload = {
            'total': self.level.amount,
            'currency': 'EUR',
            'custom_payment_id': self.level.id,
            'success_url': 'https://{}{}?globee=success'.format(
                Site.objects.get(pk=settings.SITE_ID).domain, reverse('users:donate')),
            'cancel_url': 'https://{}{}?globee=cancel'.format(
                Site.objects.get(pk=settings.SITE_ID).domain, reverse('users:donate')),
            'notification_email': 'info@scholarium.at',
        }
        response = requests.post(
            'https://globee.com/payment-api/v1/payment-request', headers=headers, data=payload).json()

        if response.get('success') is True:
            self.id = response['data']['id']
            self.approval_url = response['data']['redirect_url']
            return True
        else:
            logger.error('Globee payment failed.')
            return None
