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
    default_amount = models.SmallIntegerField(null=True, blank=True)
    purchasable_at = models.SmallIntegerField(default=0)  # Donation amount at with item can be purchased
    accessible_at = models.SmallIntegerField(null=True, blank=True)  # Donation amount at with item can be accessed
    buy_once = models.BooleanField(default=False)  # If True, item can only be purchased once
    expires_on_product_date = models.BooleanField(default=False)  # Item is only visible/purchasable until product.date
    buy_unauthenticated = models.BooleanField(default=False)  # Item is visible/purchasable for unauthenticated users
    inform_staff = models.BooleanField(default=False)  # Inform staff if item is bought

    def __str__(self):
        return f'{self.title} ({self.slug})'

    class Meta:
        verbose_name = 'Item Typ'
        verbose_name_plural = 'Item Typen'


class Item(TimeStampedModel):
    """
    Items have 3 independent states in relation to a user:
    - accessability: Can be accessed, attachments can be downloaded, etc.
    - purchasability: One of
        - purchasable
        - level required
        - purchased
        - accessible
        - requestable
        - sold out
        - unavailable
    - visibility (of purchasability state)
    """

    title = models.CharField(max_length=50, blank=True)
    type = models.ForeignKey(ItemType, on_delete=models.CASCADE, verbose_name='Typ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    _price = models.SmallIntegerField('Preis', null=True, blank=True)
    amount = models.IntegerField('Anzahl', null=True, blank=True)  # Unlimited if None
    requests = models.ManyToManyField('users.Profile', related_name='item_requests', blank=True, editable=False)
    files = models.ManyToManyField('products.FileAttachment', blank=True)
    _expires = models.DateField(null=True, blank=True)

    @property
    def expires(self):
        if self._expires:
            return self._expires
        if self.type.expires_on_product_date:
            return getattr(self.product.type, 'date', None)

    @property
    def price(self):
        return self._price or self.type.default_price

    @property
    def expired(self):
        return self.expires and self.expires < date.today()

    @property
    def sold_out(self):
        return self.amount is not None and self.amount <= 0

    @property
    def available(self):
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

    def get_status(self, user):
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

        if self.expired:
            return states[6]
        elif self.is_purchased(user) and self.type.buy_once:
            return states[2]
        elif self.donationlevel_accessible(user):
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
        elif not self.donationlevel_purchasable(user):
            return states[1]
        else:
            return states[0]

    def donationlevel_purchasable(self, user):
        if user.is_authenticated:
            return user.profile.amount >= self.type.purchasable_at
        return 0 >= self.type.purchasable_at

    def donationlevel_accessible(self, user):
        if self.type.accessible_at:
            if user.is_authenticated:
                return user.profile.amount >= self.type.accessible_at
            else:
                return 0 >= self.type.accessible_at
        return False

    def is_visible(self, user):
        if self.expired:
            return False
        if user.is_authenticated:
            return not (self.is_accessible(user) and self.attachments)
        else:
            return self.type.buy_unauthenticated

    def is_purchased(self, user):
        if user.is_authenticated:
            return bool(user.profile.purchases.filter(item=self))
        return False

    def amount_purchased(self, user):
        if user.is_authenticated:
            return sum(p.amount for p in user.profile.purchases.filter(item=self))
        return 0

    def is_accessible(self, user):
        return self.donationlevel_accessible(user) or self.is_purchased(user)

    def request(self, user):
        if user.is_authenticated:
            if self.type.request_price or self.type.additional_supply:
                self.requests.add(user.profile)
                edit_url = reverse_lazy('admin:products_item_change', args=[self.pk])
                mail_managers(
                    f'Anfrage: {self.product}',
                    f'Nutzer {user.profile} hat {self.product} im Format {self.type} angefragt. '
                    f'Das Item kann unter folgender URL editiert werden: {settings.DEFAULT_DOMAIN}{edit_url}')
                logger.debug(f'User {user.profile} requested item {self} of {self.product}')
        else:
            raise NotImplementedError()

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
        if self.get_purchasability(profile.user) == 'purchasable':
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

    def save(self, *args, **kwargs):
        if not (self.pk or self.amount):
            self.amount = self.type.default_amount
        super().save(*args, **kwargs)

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
        state = self.item.get_purchasability(self.profile.user)
        if state == 'purchasable':
            if self.profile.spend(self.total):
                if self.item.sell(self.amount):
                    if self.item.type.inform_staff:
                        mail_managers(
                            f'Neuer Kauf: {self.item.product}',
                            f'Nutzer {self.profile} hat {self.item.product} ({self.item.type}) gekauft.')
                    if self.item.type.shipping:
                        mail_managers(
                            f'Versand notwendig: {self.item.product}',
                            f'Nutzer {self.profile} hat {self.item.product} im Format {self.item.type} bestellt. '
                            f'Adresse: {self.profile.address}')
                    self.executed = True
                    self.date = date.today()
                    self.save()
                    return True
                else:
                    self.profile.refill(self.total)
        else:
            logger.warning(f'Cannot execute purchase: item state: {state}')
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
        product = next(i.product for i in self.item_set.all() if i.product.type)
        response = HttpResponse(self.file, content_type=f'application/{self.type.slug}')
        response['Content-Disposition'] = f'attachment; \
            filename={slugify(product.type.title)}.{self.type.slug}'
        return response

    def __str__(self):
        return f'{self.type.__str__()}: {self.file.name}'

    class Meta:
        verbose_name = 'Anhang'
        verbose_name_plural = 'Anhänge'
