from django.db import models
from django.core.urlresolvers import reverse

from django_extension.db.models import TimeStampedModel, TitleDescriptionModel

from products.models import Purchase, ProductBase


class EventType(TitleDescriptionModel):
    time_start = models.TimeField()
    time_end = models.TimeField()

    class Meta:
        verbose_name = 'Veranstaltungsart'
        verbose_name_plural = "Veranstaltungsarten"


class Event(ProductBase):
    date = models.DateField()
    type = models.ForeignKey(EventType)

    class Meta:
        verbose_name = "Veranstaltung"
        verbose_name_plural = "Veranstaltungen"

    def get_absolute_url(self):
        return reverse('events:%s' % self.type.name, [self.slug])

    def __str__(self):
        return '%s: %s' % (self.type.name, self.name)


class Livestream(TimeStampedModel):
    purchase = models.OneToOneRel(Purchase, on_delete=models.CASCADE)
    link = models.CharField(max_length=100)
    chat = models.BooleanField(default=False)

    def embed_link(self):
        return self.link.replace('watch?v=', 'embed/')
