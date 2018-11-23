import logging
from slugify import slugify
from datetime import date

from django.db import models
from django.db.models import Q
from django.core.mail import mail_managers, send_mail
from django.urls import reverse_lazy
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string

from django_extensions.db.models import TimeStampedModel, TitleDescriptionModel, TitleSlugDescriptionModel

from framework.behaviours import CommentAble
from .behaviours import AttachmentBase


logger = logging.getLogger(__name__)


class Product(models.Model):
    """Class to avoid MTI/generic relations: Explicit OneToOneField with all products."""

    @property
    def type(self):
        """Get product object"""
        for product_rel in self._meta.get_fields():
            if product_rel.one_to_one and getattr(self, product_rel.name, False):
                return getattr(self, product_rel.name)

    def items_accessible(self, profile):
        """Returns items that can be accessed by user"""
        return self.item_set.filter(
            Q(purchase__in=profile.purchases) | Q(type__accessible_at__lt=profile.amount)).distinct()

    def any_attachments_accessible(self, profile):
        """Only checks for existence for performance reasons"""
        for item in self.items_accessible(profile):
            if item.attachments:
                return True

    def __str__(self):
        return self.type.__str__()

    class Meta:
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkte'


class ItemType(TitleDescriptionModel, TimeStampedModel):
    slug = models.SlugField()
    shipping = models.BooleanField(default=False)  # Calculate shipping at checkout
    request_price = models.BooleanField(default=False)  # Can be requested when item has no price
    additional_supply = models.BooleanField(default=False)  # Can be requested when item is sold out
    default_price = models.SmallIntegerField(null=True, blank=True)
    purchasable_at = models.SmallIntegerField(default=0)  # Donation amount at with item can be purchased
    accessible_at = models.SmallIntegerField(null=True, blank=True)  # Donation amount at with item can be accessed
    unavailability_notice = models.CharField(max_length=20, default="Nicht verfügbar")  # TODO: Remove?
    buy_once = models.BooleanField(default=False)  # If True, item can only be purchased once
    expires_on_product_date = models.BooleanField(default=False)  # Item is only visible/purchasable until product.date
    buy_unauthenticated = models.BooleanField(default=False)  # Item is visible/purchasable for unauthenticated users

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Item Typ'
        verbose_name_plural = 'Item Typen'


class Item(TimeStampedModel):
    """
    Items are purchasable can have 3 states in relation to a user:
    - requestable: Is visible and can be requested.
    - purchasable: Can be purchased.
    - accessible: Can be accessed, attachments can be downloaded, etc.
    If amount is None, the item is unlimited.
    """

    title = models.CharField(max_length=50, blank=True)
    type = models.ForeignKey(ItemType, on_delete=models.CASCADE, verbose_name='Typ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    _price = models.SmallIntegerField('Preis', null=True, blank=True)
    amount = models.IntegerField('Anzahl', null=True, blank=True)
    requests = models.ManyToManyField('users.Profile', related_name='item_requests', blank=True, editable=False)
    files = models.ManyToManyField('products.FileAttachment', blank=True)
    _expires = models.DateField(null=True, blank=True)

    @property
    def expires(self):
        if self.type.expires_on_product_date:
            return getattr(self.product.type, 'date', None)
        return self._expires

    @property
    def price(self):
        return self._price or self.type.default_price

    @property
    def expired(self):
        return self.expires and self.expires < date.today()

    @property
    def sold_out(self):
        return self.amount and self.amount <= 0

    @property
    def available(self):  # TODO: Remove
        return self.price and not self.expired and not self.sold_out

    @property
    def attachments(self):
        # TODO: Remove? Custom attachments should maybe be handled individually when needed.
        """Fetches related attachments """
        attachment_list = []
        for item_rel in self._meta.get_fields():
            if item_rel.related_model and issubclass(item_rel.related_model, AttachmentBase)\
                    and getattr(self, item_rel.get_accessor_name(), False):
                attachment_list += (getattr(self, item_rel.get_accessor_name()).all())
        return list(self.files.all()) + attachment_list

    def get_state(self, user):
        state = {
            'accessible': self.is_accessible(user),
            'purchasability': self.get_purchasability(user),
            'visible': self.is_visible(user)
        }
        return state

    def get_purchasability(self, user):
        """
        Returns purchaseability state if an item.
        This is unrelated to the visibility or accessibility of the item.
        """

        states = [
            'purchasable',
            'level required',
            'purchased',
            'accessible',
            'requestable',
            'sold out',
            'unavailable'
        ]

        # if self.is_purchasable(user):
        #     return 'purchasable'
        # elif self.is_requestable(user):
        #     return 'requestable'
        # elif self.is_purchased(user) and self.type.buy_once:
        #     return 'purchased'
        # elif self.sold_out:
        #     return 'sold out'
        # elif profile.get('amount', 0) < self.type.purchasable_at:
        #     return 'level required'
        # elif self.expired:
        #     return 'unavailable'

        profile = user.get('profile', {})
        if self.expired:
            return states[6]
        elif self.is_purchased(user) and self.buy_once:
            return states[2]
        elif profile.get('amount', 0) < self.type.accessible_at:
            return states[3]
        elif self.sold_out:
            if self.type.additional_supply and user.is_authenticated:
                return states[4]
            else:
                return states[5]
        elif not self.price:
            if self.type.request_price and user.is_authenticated:
                return states[4]
            else:
                return states[6]
        elif profile.get('amount', 0) < self.type.purchasable_at:
            return states[1]
        else:
            return states[0]

    def is_purchased(self, user):
        if user.is_authenticated:
            return bool(user.profile.purchases.filter(item=self))
        return False

    def is_accessible(self, user):
        if user.is_authenticated:
            return user.profile.amount >= self.type.accessible_at if self.type.accessible_at is not None else \
                self.is_authenticated(user)
        return False

    def is_visible(self, user):
        if self.expired:
            return None
        return user.is_authenticated or self.type.buy_unauthenticated

    def is_requestable(self, user):  # TODO: Remove
        return not self.available and \
            profile.amount >= self.type.purchasable_at and \
            self.type.requestable and \
            self.amount > 0 or self.type.additional_supply

    def is_purchasable(self, user):  # TODO: Remove
        if user.is_authenticated:
            return self.available and user.profile.amount >= self.type.purchasable_at and \
                not (self.is_accessible(user.profile) and self.type.buy_once)
        else:
            return self.available and self.type.buy_unauthenticated \
                and self.type.purchasable_at == 0

    def amount_purchased(self, user):
        if user.is_authenticated:
            return sum(p.amount for p in user.profile.purchases.filter(item=self))
        return 0

    def amount_accessible(self, user):  # TODO: Remove?
        return 1 if self.type.accessible_at is not None and profile.amount >= self.type.accessible_at else \
            self.amount_purchased(profile)

    def request(self, profile):
        if self.type.requestable:
            self.requests.add(profile)
            edit_url = reverse_lazy('admin:products_item_change', args=[self.pk])
            mail_managers(
                f'Anfrage: {self.product}',
                f'Nutzer {profile} hat {self.product} im Format {self.type} angefragt. '
                f'Das Item kann unter folgender URL editiert werden: {settings.DEFAULT_DOMAIN}{edit_url}')

    def inform_users(self):
        user_addresses = [profile.user.email for profile in self.requests.all()]
        send_mail(
            f'Verfügbarkeit: {self.product}',
            render_to_string('products/emails/availability_email.txt', {'item': self}),
            settings.DEFAULT_FROM_EMAIL,
            user_addresses,
            fail_silently=False,
            html_message=render_to_string('products/emails/availability_email.html', {'item': self})
        )
        logger.debug(f'Informed users {self.requests.all()} of availability of {self.product} as {self}')
        self.requests.clear()

    def add_to_cart(self, profile):
        """Only add a limited product if no purchase of it exists."""
        if self.is_purchasable(profile):
            purchase, created = Purchase.objects.get_or_create(profile=profile, item=self, executed=False)
            if not created:
                purchase.amount += 1
                purchase.save()
            return True

    def sell(self, amount):
        """Given an amount, tries to lower local amount. Ignored if not limited."""
        if self.amount is not None:
            new_amount = self.amount - amount
            if new_amount >= 0:
                self.amount = new_amount
                self.save()
                return True
            else:
                logger.exception(f"Can't sell item: {self.amount} < {amount}")
                return False
        else:
            return True

    def refill(self, amount):
        """Refills amount."""
        if self.amount is not None:
            self.amount += amount
            self.save()

    def __str__(self):
        if self.title:
            return f'{self.type.title}: {self.title}'
        return self.type.title

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'


class Purchase(TimeStampedModel, CommentAble):
    """Logs purchases."""

    profile = models.ForeignKey('users.Profile', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.SmallIntegerField(default=1)
    shipped = models.DateField(blank=True, null=True)
    executed = models.BooleanField(default=False)
    free = models.BooleanField(default=False)
    date = models.DateField(null=True, blank=True)

    @property
    def total(self):
        return 0 if self.free else self.item.price * self.amount

    @property
    def available(self):
        """Check if required amount is available"""
        return self.item.available and self.item.amount >= self.amount

    def execute(self):
        if self.item.is_purchasable(self.profile):
            if self.profile.spend(self.total):
                if self.item.sell(self.amount):
                    if self.item.type.shipping:
                        mail_managers(
                            f'Bestellung: {self.item.product}',
                            f'Nutzer {self.profile} hat {self.item.product} im Format {self.item.type} bestellt. '
                            f'Adresse: {self.profile.address}')
                    self.executed = True
                    self.date = date.today()
                    self.save()
                    return True
                else:
                    self.profile.refill(self.total)
        return False

    def revert(self):
        self.profile.refill(self.total)
        self.item.refill(self.amount)
        self.delete()

    def __str__(self):
        return '%dx %s (%s)' % (self.amount, self.item.product.__str__(), self.profile.__str__())

    class Meta():
        verbose_name = 'Kauf'
        verbose_name_plural = 'Käufe'


class AttachmentType(TitleSlugDescriptionModel):
    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Anhangstyp'
        verbose_name_plural = 'Anhangstypen'


class FileAttachment(models.Model):
    file = models.FileField()
    type = models.ForeignKey('products.AttachmentType', on_delete=models.PROTECT)

    def get(self):
        print(self.file)
        response = HttpResponse(self.file, content_type=f'application/{self.type.slug}')
        response['Content-Disposition'] = f'attachment; \
            filename={slugify(self.item.product)}.{self.type.slug}'
        return response

    def __str__(self):
        return f'{self.type.__str__()}: {self.file.name}'

    class Meta:
        verbose_name = 'Anhang'
        verbose_name_plural = 'Anhänge'
