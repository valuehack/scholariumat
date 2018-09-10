from datetime import time

from django.db import models
from django.urls import reverse

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from products.models import Item
from products.behaviours import ProductBase
from framework.behaviours import PublishAble


class EventType(TitleSlugDescriptionModel):

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Veranstaltungsart'
        verbose_name_plural = "Veranstaltungsarten"


class Event(ProductBase, PublishAble):
    """Events are not directly purchasable products."""

    date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    type = models.ForeignKey(EventType, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Veranstaltung"
        verbose_name_plural = "Veranstaltungen"

    def get_absolute_url(self):
        return reverse('events:event', kwargs={'slug': self.slug})

    def __str__(self):
        return '%s: %s' % (self.type.title, self.title)


class Livestream(TimeStampedModel):
    """Every livestream is an purchasable item."""

    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    link = models.CharField(max_length=100)
    chat = models.BooleanField(default=False)
    time_start = models.TimeField(default=time(hour=19))

    @property
    def link_embedded(self):
        return self.link.replace('watch?v=', 'embed/')

    def __str__(self):
        return f"Livestream: {self.item.product}"
