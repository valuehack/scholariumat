from django.db import models
from django.urls import reverse

from django_extensions.db.models import TitleDescriptionModel

from donations.models import DonationLevel


class Menu(models.Model):
    pass


class MenuBase(TitleDescriptionModel):
    id = models.IntegerField(primary_key=True)
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
