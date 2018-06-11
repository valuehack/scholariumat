from importlib import import_module

from django.db import models
from django.urls import reverse


class CommentAble(models.Model):
    comment = models.TextField(blank=True)

    class Meta:
        abstract = True


class PublishAble(models.Model):
    publish_date = models.DateField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['-publish_date']  # TODO: effect?


class PermalinkAble(models.Model):
    """Attempt to universalize get_absolute_url. Uses pattern app_name:class_name and a slug keyword argument."""

    def get_absolute_url(self):
        app_name = getattr(import_module('..urls', self.__class__.__module__), 'app_name')
        class_name = self.__class__.__name__.lower()
        return reverse("%s:%s" % (app_name, class_name), kwargs={'slug': self.slug})

    class Meta:
        abstract = True
