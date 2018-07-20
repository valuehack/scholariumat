from django.db import models
from django.db.models import Q
from django.urls import reverse

from django_extensions.db.models import TitleDescriptionModel, TitleSlugDescriptionModel

from donations.models import DonationLevel


class Menu(TitleSlugDescriptionModel):

    def get_items(self, request):
        donation_amount = request.user.profile.amount
        return self.menuitem_set.filter(
            Q(min_level__isnull=True) | Q(min_level__amount__lte=donation_amount),
            Q(max_level__isnull=True) | Q(max_level__amount__gt=donation_amount))

    def __str__(self):
        return self.title


class MenuBase(TitleDescriptionModel):
    ordering = models.SmallIntegerField('Reihenfolge')
    url_name = models.CharField('URL Name', max_length=50)

    def get_absolute_url(self):
        return reverse(self.url_name)

    class Meta:
        abstract = True
        ordering = ['ordering']


class MenuItem(MenuBase):
    min_level = models.ForeignKey(
        DonationLevel, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Sichtbar ab', related_name='menuitem_min')
    max_level = models.ForeignKey(
        DonationLevel, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Sichtbar bis (nicht eingeschlossen)', related_name='menuitem_max')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)


class MenuSubItem(MenuBase):
    parent = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
