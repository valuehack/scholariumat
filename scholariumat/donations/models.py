import datetime
import logging
import uuid
import requests

from django.db import models
from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel
import paypalrestsdk as paypal

from framework.behaviours import CommentAble


logger = logging.getLogger(__name__)


class DonationLevel(TitleSlugDescriptionModel):
    amount = models.SmallIntegerField(unique=True)

    @classmethod
    def get_level_by_amount(cls, amount):
        level = cls.objects.filter(amount__lte=amount).order_by('-amount')
        if level:
            return level[0]
        else:
            logger.info("No level available for {}".format(amount))

    @classmethod
    def get_lowest_amount(cls):
        level = cls.objects.all().order_by('-amount')
        return level[0].amount if level else None

    class Meta:
        verbose_name = 'Spendenstufe'
        verbose_name_plural = 'Spendenstufen'

    def __str__(self):
        return '{}: {}'.format(self.amount, self.title)


class PaymentMethod(TitleSlugDescriptionModel):
    return_url_name = models.CharField(max_length=50, default='donations:approve')

    @property
    def return_url(self):
        return HttpRequest.build_absolute_uri(reverse(self.return_url_name))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Zahlungsmethode'
        verbose_name_plural = 'Zahlungsmethoden'


class Payment(CommentAble, TimeStampedModel):
    slug = models.SlugField(max_length=100, null=True, blank=True, unique=True)
    amount = models.SmallIntegerField()
    method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    executed = models.BooleanField(default=False)
    review = models.BooleanField(default=False)
    approval_url = models.CharField(max_length=200, blank=True)

    def init(self):
        """Creates payment and sets id and approval url."""
        if self.method.slug == 'paypal':
            success = self._create_paypal(self.amount)
        elif self.method.slug == 'globee':
            success = self._create_globee(self.amount)
        else:
            self.slug = uuid.uuid4().hex.upper()
            self.approval_url = reverse('donations:approve', kwargs={'slug': self.slug})
            self.save()
            success = True

        if success:
            logger.debug("Payment {} created successfully".format(self.slug))
            return True

    def _create_paypal(self):
        level = DonationLevel.get_level_by_amount(self.amount)
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
            return True
        else:
            logger.exception("Payment creation failed. Paypal returned {}".format(payment.error))

    def _create_globee(self):
        level = DonationLevel.get_level_by_amount(self.amount)
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
            return True
        else:
            logger.error('Globee payment failed.')

    def execute(self, request):
        """
        Takes request object returned from approval urls, containing necessary execution information.
        Executes/Checks payment and creates Donation.
        """
        if not self.executed:
            if self.method == 'paypal':
                success = self._execute_paypal(request)
            if self.method == 'globee':
                success = self._execute_globee(request)
            else:  # Payment to be checked manually instead
                success = True

            if success:
                logger.debug("Payment {} executed successfully".format(self.slug))
                request.user.profile.donate(self.amount, {'payment': self})
                self.executed = True
                self.save()
                return True

    def _execute_paypal(self, request):
        paypal.configure(settings.PAYPAL_SETTINGS)
        payment = paypal.Payment.find(self.slug)
        return payment.execute({"payer_id": request.GET['PayerID']})

    def _execute_globee(self, request):
        headers = {
            'Accept': 'application/json',
            'X-AUTH-KEY': settings.GLOBEE_API_KEY}
        payment = requests.get(
            'https://globee.com/payment-api/v1/payment-request/{}'.format(self.slug), headers=headers).json()
        if payment.get('success') is True:
            status = payment['data'].get('status')
            if status == 'confirmed' or status == 'paid':
                return True


class Donation(CommentAble, TimeStampedModel):
    """Enables user to use services according to active donation level."""
    @staticmethod
    def _default_expiration():
        return datetime.date.today() + datetime.timedelta(days=settings.DONATION_PERIOD)

    profile = models.ForeignKey('users.Profile', on_delete=models.CASCADE)
    amount = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    expiration = models.DateField(default=_default_expiration.__func__)
    payment = models.OneToOneField(Payment, null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def level(self):
        return DonationLevel.get_level_by_amount(self.amount)

    def __str__(self):
        return '%s: %s (%s)' % (self.profile.name, self.level.title, self.date)

    class Meta:
        verbose_name = 'Unterstützung'
        verbose_name_plural = 'Unterstuetzungen'
