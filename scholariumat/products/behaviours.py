import logging
import uuid
import requests
import paypalrestsdk as paypal

from django.db import models
from django.conf import settings
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel
from django.urls import reverse_lazy
from django.core.mail import mail_managers


from framework.behaviours import CommentAble, PermalinkAble


logger = logging.getLogger(__name__)


class ProductBase(TitleSlugDescriptionModel, TimeStampedModel, PermalinkAble):
    """Abstract parent class for all product type classes."""

    product = models.OneToOneField('products.Product', on_delete=models.CASCADE, null=True, editable=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.product:
            from .models import Product
            self.product = Product.objects.create()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # TODO: Gets ignored in bulk delete. pre_delete signal better?
        self.product.delete()
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True


class AttachmentBase(models.Model):
    """Base class to create downloadable item attachment classes."""

    type = models.ForeignKey('products.AttachmentType', on_delete=models.PROTECT)
    item = models.ForeignKey('products.Item', on_delete=models.CASCADE, null=True, blank=True)

    def get(self):
        pass

    def __str__(self):
        item_type = self.item.type.__str__()
        type = self.type.__str__()
        return f'{item_type}: {type}' if item_type != type else type

    class Meta:
        abstract = True


class BalanceMixin(models.Model):
    """Profile mixin for storing and managing user balance"""

    balance = models.SmallIntegerField('Guthaben', default=0)

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

    class Meta:
        abstract = True


class CartMixin(models.Model):
    """Profile mixin for storing and processing items in a shopping cart"""

    @property
    def cart(self):
        return self.purchase_set.filter(executed=False).order_by('-created')\
            .select_related('item__type').select_related('item__product')

    @property
    def cart_shipping(self):
        """Returns shipping costs of cart."""
        return settings.SHIPPING if any([purchase.item.type.shipping for purchase in self.cart]) else 0

    @property
    def cart_total(self):
        """Sums prices and adds shiping costs"""
        return sum([purchase.total for purchase in self.cart]) + self.cart_shipping

    @property
    def cart_available(self):
        return all([purchase.available for purchase in self.cart])

    def clean_cart(self):
        for purchase in self.purchase_set.filter(executed=False):
            if not purchase.available:
                purchase.delete()

    def execute_cart(self):
        if self.balance >= self.cart_total:
            for purchase in self.cart:
                purchase.execute()
            return True

    @property
    def purchases(self):
        return self.purchase_set.filter(executed=True).order_by('-modified')\
            .select_related('item__type').select_related('item__product')

    @property
    def items_bought(self):
        from .models import Item
        return Item.objects.filter(purchase__in=self.purchases).distinct()

    @property
    def products_bought(self):
        from .models import Product
        return Product.objects.filter(item__in=self.items_bought).distinct()

    @property
    def orders(self):
        return self.purchases.filter(amount__isnull=False)

    @property
    def events_booked(self):
        return self.purchases.filter(item__type__slug__in=['livestream', 'teilnahme'])

    class Meta:
        abstract = True


class PayAble(CommentAble):
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
        return '{}{}'.format(settings.DEFAULT_DOMAIN, reverse_lazy('products:approve', kwargs={'slug': self.slug}))

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
                        "name": 'Unterstützung',
                        "sku": self.slug,
                        "price": self.amount,
                        "currency": "EUR",
                        "quantity": 1}]},
                "amount": {
                    "total": self.amount,
                    "currency": "EUR"},
                "description": 'Unterstützung'}]}

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
                mail_managers(
                    f'Neue Zahlung: {self.amount}€',
                    f'Nutzer {self.profile} hat {self.amount} Euro per {self.method} gezahlt. ')
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


class PaymentProfileMixin(models.Model):
    def clean_payments(self):
        self.payment_set.filter(executed=False).delete()

    class Meta:
        abstract = True
