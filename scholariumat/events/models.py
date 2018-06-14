from django.db import models
from django.urls import reverse

from django_extensions.db.models import TimeStampedModel, TitleDescriptionModel

from products.models import Item, ProductBase
from framework.behaviours import PublishAble


class EventType(TitleDescriptionModel):
    time_start = models.TimeField()
    time_end = models.TimeField()

    class Meta:
        verbose_name = 'Veranstaltungsart'
        verbose_name_plural = "Veranstaltungsarten"


class Event(ProductBase, PublishAble):
    """Events are not directly purchable products."""

    date = models.DateField()
    type = models.ForeignKey(EventType, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Veranstaltung"
        verbose_name_plural = "Veranstaltungen"

    def get_absolute_url(self):
        return reverse('events:%s' % self.type.name, [self.slug])

    def __str__(self):
        return '%s: %s' % (self.type.name, self.name)


class Livestream(TimeStampedModel):
    """Every livestream is an purchaseable item."""

    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    link = models.CharField(max_length=100)
    chat = models.BooleanField(default=False)

    @property
    def link_embedded(self):
        return self.link.replace('watch?v=', 'embed/')
