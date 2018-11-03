from datetime import date, datetime, timedelta
import logging

from django.db import models
from django.conf import settings
from django.urls import reverse

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from products.models import Item, ItemType, AttachmentType, FileAttachment
from products.behaviours import ProductBase
from framework.behaviours import PublishAble
from framework.managers import PublishedManager


logger = logging.getLogger(__name__)


class EventType(TitleSlugDescriptionModel):
    section_title = models.CharField(max_length=50, blank=True)
    default_time_start = models.TimeField(null=True, blank=True)
    default_time_end = models.TimeField(null=True, blank=True)

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
    old_pk = models.SmallIntegerField(null=True, blank=True)

    @property
    def time_start(self):
        return self._time_start or self.type.default_time_start

    @property
    def time_end(self):
        return self._time_end or self.type.default_time_end

    @property
    def livestream(self):
        livestreams = Livestream.objects.filter(item__product__event=self)
        return livestreams[0] if livestreams else None

    def update_or_create_livestream(self, link):
        item_type = ItemType.objects.get(slug='livestream')
        item, created = self.product.item_set.get_or_create(type=item_type)
        livestream, created = Livestream.objects.update_or_create(item=item, defaults={'link': link})
        logger.debug(f'Livestream for {self} saved.')
        return item

    def get_or_create_attendance(self):
        item_type = ItemType.objects.get(slug='attendance')
        item, created = self.product.item_set.get_or_create(type=item_type)
        logger.debug(f'Attendance item for {self} saved.')
        return item

    def get_or_create_recording(self, recording):
        item_type = ItemType.objects.get(slug='recording')
        attachment_type = AttachmentType.objects.get(slug='mp3')
        item, created = self.product.item_set.get_or_create(type=item_type)
        attachment, created = FileAttachment.objects.get_or_create(type=attachment_type, file=recording)
        item.files.add(attachment)
        livestream = self.livestream
        if livestream:
            livestream.item.files.add(attachment)
        logger.debug(f'Attachment for {self} saved.')
        return item

    def publish(self):
        self.create_attendance_item()
        super().publish()

    def get_absolute_url(self):
        return reverse('events:event', kwargs={'slug': self.slug})

    def __str__(self):
        return '%s: %s' % (self.type.title, self.title)

    class Meta:
        ordering = ['-date']
        verbose_name = "Veranstaltung"
        verbose_name_plural = "Veranstaltungen"


class Livestream(TimeStampedModel):
    """Every livestream is a purchasable item."""

    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    link = models.CharField(max_length=100)
    chat = models.BooleanField(default=False)

    @property
    def link_embedded(self):
        return self.link.replace('watch?v=', 'embed/')

    @property
    def show(self):
        event = self.item.product.event
        if event.time_start:
            event_start = datetime.combine(event.date, event.time_start)
            if datetime.now() + timedelta(minutes=settings.SHOW_LIVESTREAM) >= event_start:
                return True
        else:
            return True if event.date <= date.today() else False

    def __str__(self):
        return f"Livestream: {self.item.product}"
