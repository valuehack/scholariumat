from django.db import models
from django.urls import reverse

from donations.models import Donation


class Menu(models.Model):
    levels = models.ManyToManyField(Donation)


class MenuBase(models.Model):
    title = models.CharField(max_length=50)
    target = models.CharField(max_length=50)

    def get_absolute_url(self):
        return reverse(self.target)

    class Meta:
        abstract = True


class MenuItem(MenuBase):
    id = models.IntegerField(primary_key=True)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']


class MenuSubItem(MenuBase):
    parent = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
