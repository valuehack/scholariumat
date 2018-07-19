from django.db import models
from django.urls import reverse

from django_extensions.db.models import TitleDescriptionModel, TitleSlugDescriptionModel

from donations.models import DonationLevel


class Menu(TitleSlugDescriptionModel):

    def get_items(self, level):
        return self.MenuItem_set.filter(levels__id=level.id)

    def __str__(self):
        return self.title


class MenuBase(TitleDescriptionModel):
    ordering = models.SmallIntegerField()
    levels = models.ManyToManyField(DonationLevel)
    title = models.CharField(max_length=50)
    target = models.CharField(max_length=50)

    def get_absolute_url(self):
        return reverse(self.target)

    class Meta:
        abstract = True
        ordering = ['id']


class MenuItem(MenuBase):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)


class MenuSubItem(MenuBase):
    parent = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
