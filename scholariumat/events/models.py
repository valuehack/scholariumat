from datetime import date, datetime, timedelta
import logging

from django.db import models
from django.conf import settings
from django.urls import reverse

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from products.behaviours import ProductBase, ProductContent
from framework.behaviours import PublishAble
from framework.managers import PublishedManager


logger = logging.getLogger(__name__)


class EventType(TitleSlugDescriptionModel):
    section_title = models.CharField(max_length=50, blank=True)
    default_time_start = models.TimeField(null=True, blank=True)
    default_time_end = models.TimeField(null=True, blank=True)

    @property
    def header(self):
        return self.section_title or self.title

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Veranstaltungsart'
        verbose_name_plural = "Veranstaltungsarten"


class Event(ProductBase, PublishAble):
    """Events are not directly purchasable products."""

    objects = PublishedManager()

    date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    type = models.ForeignKey(EventType, on_delete=models.PROTECT)
    _time_start = models.TimeField(null=True, blank=True)
    _time_end = models.TimeField(null=True, blank=True)
    old_pk = models.SmallIntegerField(null=True, blank=True, editable=False)

    @property
    def time_start(self):
        return self._time_start or self.type.default_time_start

    @property
    def time_end(self):
        return self._time_end or self.type.default_time_end

    @property
    def livestream(self):
        return self.product.livestream_set.first()

    def get_absolute_url(self):
        return reverse('events:event', kwargs={'slug': self.slug})

    def __str__(self):
        return '%s: %s' % (self.type.title, self.title)

    class Meta:
        ordering = ['-date']
        verbose_name = "Veranstaltung"
        verbose_name_plural = "Veranstaltungen"


class Livestream(TimeStampedModel, ProductContent):
    link = models.CharField(max_length=100)
    chat = models.BooleanField(default=False)

    @property
    def link_embedded(self):
        return self.link.replace('watch?v=', 'embed/')

    @property
    def show(self):
        event = self.product.event
        if event.time_start:
            event_start = datetime.combine(event.date, event.time_start)
            if datetime.now() + timedelta(minutes=settings.SHOW_LIVESTREAM) >= event_start:
                return True
        else:
            return True if event.date <= date.today() else False

    @property
    def show_chat(self):
        return self.chat and self.show and self.product.event.date == date.today()

    def __str__(self):
        return f"Livestream: {self.product.event}"
