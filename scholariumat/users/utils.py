import logging
import random
import string
import requests

from django.urls import reverse
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.staticfiles.templatetags.staticfiles import static

import paypalrestsdk

from .models import DonationLevel


logger = logging.getLogger(__name__)


def get_paypal_payment(amount):
    paypalrestsdk.configure({
        "mode": settings.PAYPAL_MODE,
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET})

    # Gets Paypal Web Profile
    wpn = ''.join(random.choice(string.ascii_uppercase) for i in range(12))
    web_profile = paypalrestsdk.WebProfile({
        "name": wpn,
        "presentation": {
            "brand_name": "scholarium",
            "logo_image": "https://" + Site.objects.get(pk=settings.SITE_ID).domain + static('img/scholarium_et.jpg'),
            "locale_code": "AT"
        },
        "input_fields": {
            "allow_note": True,
            "no_shipping": 1,
            "address_override": 1
        },
        "flow_config": {
            "landing_page_type": "login",
            "bank_txn_pending_url": 'https://' + Site.objects.get(pk=settings.SITE_ID).domain + reverse('users:donate'),
            "user_action": "commit"
        }})
    if web_profile.create():
        logger.debug("Web Profile[{}] created successfully".format(web_profile.id))
    else:
        logger.exception("Paypal returned {}".format(web_profile.error))

    level = DonationLevel.get_level_by_amount(amount)
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "experience_profile_id": web_profile.id,
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": 'https://' + Site.objects.get(pk=settings.SITE_ID).domain + reverse('users:donate') + '?paypal=success',
            "cancel_url": 'https://' + Site.objects.get(pk=settings.SITE_ID).domain + reverse('users:donate') + '?paypal=cancel'},
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
            "description": level.title}]})

    if payment.create():
        logger.debug("Payment[%s] created successfully" % (payment.id))
        return payment
    else:
        logger.exception("Paypal returned {}".format(payment.error))


def get_globee_payment(amount):
    level = DonationLevel.get_level_by_amount(amount)

    headers = {
        'Accept': 'application/json',
        'X-AUTH-KEY': settings.GLOBEE_API_KEY,
    }
    payload = {
        'total': level.amount,
        'currency': 'EUR',
        'custom_payment_id': level.id,
        'success_url': 'https://' + Site.objects.get(pk=settings.SITE_ID).domain + reverse('users:donate') + '?globee=success',
        'cancel_url': 'https://' + Site.objects.get(pk=settings.SITE_ID).domain + reverse('users:donate') + '?globee=cancel',
        'notification_email': 'mb@scholarium.at',
    }
    response = requests.post('https://globee.com/payment-api/v1/payment-request', headers=headers, data=payload).json()

    if response.get('success') is True:
        return response
    else:
        logger.error('Globee payment failed.')
        return None
