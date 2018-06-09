from django.db import models

from users.models import Donation


class Menu(models.Model):
    levels = models.ManyToManyField(Donation)


class MenuItem(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    menue = models.ForeignKey(Menu, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        abstract = True
        ordering = ['id']
