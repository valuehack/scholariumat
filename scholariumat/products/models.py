import logging

from django.db import models
from django.db.models import Q
from django.core.mail import mail_managers
from django.urls import reverse_lazy
from django.conf import settings

from django_extensions.db.models import TimeStampedModel, TitleDescriptionModel

from framework.behaviours import CommentAble
from .behaviours import AttachmentBase


logger = logging.getLogger('__name__')


class Product(models.Model):
    """Class to avoid MTI/generic relations: Explicit OneToOneField with all products."""

    @property
    def type(self):
        """Get product object"""
        for product_rel in self._meta.get_fields():
            if product_rel.one_to_one and getattr(self, product_rel.name, False):
                return getattr(self, product_rel.name)

    @property
    def items_available(self):
        return self.item_set.filter(Q(price__gt=0), Q(amount__gt=0) | Q(type__limited=False))

    def __str__(self):
        return self.type.__str__()

    class Meta:
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkte'


class ItemType(TitleDescriptionModel, TimeStampedModel):
    slug = models.SlugField()
    limited = models.BooleanField(default=True)
    shipping = models.BooleanField(default=False)
    requestable = models.BooleanField(default=False)
    purchasable = models.SmallIntegerField(default=0)
    accessible = models.SmallIntegerField(null=True, blank=True)
    unavailability_notice = models.CharField(max_length=20, default="Nicht verfügbar")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Item Typ'
        verbose_name_plural = 'Item Typen'


class Item(TimeStampedModel):
    """Purchasable items."""

    type = models.ForeignKey(ItemType, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.SmallIntegerField(null=True, blank=True)
    amount = models.IntegerField(null=True, blank=True)
    requests = models.ManyToManyField('users.Profile', related_name='item_requests', blank=True)

    @property
    def available(self):
        return self.price and (self.amount or not self.type.limited)

    @property
    def attachment(self):
        """Fetches related attachment"""
        for item_rel in self._meta.get_fields():
            if item_rel.one_to_one and issubclass(item_rel.related_model, AttachmentBase) and \
               getattr(self, item_rel.name, False):
                return getattr(self, item_rel.name)

    def is_purchasable(self, profile):
        return profile.amount >= self.type.purchasable

    def is_accessible(self, profile):
        access = self.type.accessible
        return self in profile.items_bought or (access is not None and profile.amount > access)

    def download(self):
        return self.attachment.get() if self.attachment else None

    def request(self, profile):
        if self.type.requestable:
            self.requests.add(profile)
            edit_url = reverse_lazy('admin:products_item_change', args=[self.pk])
            mail_managers(
                f'Anfrage: {self.product}',
                f'Nutzer {profile} hat {self.product} im Format {self.type} angefragt. '
                f'Das Item kann unter folgender URL editiert werden: {settings.DEFAULT_DOMAIN}{edit_url}')

    def inform_users(self):
        pass
        # TODO: Send email to users in requests

    def add_to_cart(self, profile):
        """Only add a limited product if no purchase of it exists."""
        if not self.is_purchasable(profile):
            return False
        if not self.type.limited:
            purchase, created = Purchase.objects.get_or_create(profile=profile, item=self, defaults={'executed': False})
            if not created:
                return False
        else:
            purchase, created = Purchase.objects.get_or_create(profile=profile, item=self, executed=False)
            if not created:
                purchase.amount += 1
                purchase.save()
        return True

    def sell(self, amount):
        """Given an amount, tries to lower local amount. Ignored if not limited."""
        if self.type.limited:
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
        if self.type.limited:
            self.amount += amount
            self.save()

    def __str__(self):
        return '{} für {} Punkte'.format(self.type.__str__(), self.price)

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

    @property
    def total(self):
        return self.item.price * self.amount if self.item.type.limited else self.item.price

    @property
    def available(self):
        """Check if required amount is available"""
        return self.item.available and (not self.item.type.limited or self.item.amount >= self.amount)

    def execute(self):
        if self.profile.spend(self.total):
            if self.item.sell(self.amount):
                self.executed = True
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
