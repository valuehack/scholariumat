from datetime import date
import logging
import requests

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)


class CommentAble(models.Model):
    comment = models.TextField(blank=True)

    class Meta:
        abstract = True


class PublishAble(models.Model):
    """Makes a model publishable by manipulating publish_date."""

    publish_date = models.DateField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(default=0)

    def publish(self):
        self.publish_date = date.today()
        self.save()
        logger.info('{} published.'.format(self.title))

    def buffer_publish(self):
        """Publishes the object to social media via Buffer."""

        link = 'https://%s%s' % (Site.objects.get(pk=settings.SITE_ID).domain, self.get_absolute_url())
        data = [
            ('access_token', settings.BUFFER_ACCESS_TOKEN),
            ('media[link]', link)
        ]
        ids = [('profile_ids[]', id) for id in settings.BUFFER_SITE_IDS]
        payload = ids + data
        response = requests.post('https://api.bufferapp.com/1/updates/create.json', data=payload)
        logger.debug('Buffer response: {}'.format(response.text))
        response.raise_for_status()

    @classmethod
    def cron_publish(cls):
        """Publishes an instance after RELEASE_PERIOD, sorted by priority."""

        published = cls.objects.filter(publish_date__isnull=False)
        time_passed = (date.today() - published[0].publish_date).days if published else None

        if time_passed >= settings.RELEASE_PERIOD:
            unpublished = cls.objects.filter(publish_date__isnull=True)
            if unpublished:
                article = unpublished[0]
                article.publish()
                article.buffer_publish()

    class Meta:
        abstract = True
        ordering = ['-publish_date', '-priority']


class PermalinkAble(models.Model):
    """Attempt to universalize get_absolute_url. Uses pattern app_label:object_name and a slug keyword argument."""

    def get_absolute_url(self):
        app_label = self._meta.app_label
        object_name = self._meta.object_name.lower()
        return reverse("%s:%s" % (app_label, object_name), kwargs={'slug': self.slug})

    class Meta:
        abstract = True
