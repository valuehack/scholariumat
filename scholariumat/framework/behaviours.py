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
        ordering = ['-publish_date']  # TODO: to test


class PermalinkAble(models.Model):
    """Attempt to universalize get_absolute_url. Uses pattern app_label:object_name and a slug keyword argument."""

    def get_absolute_url(self):
        app_label = self._meta.app_label
        object_name = self._meta.object_name.lower()
        return reverse("%s:%s" % (app_label, object_name), kwargs={'slug': self.slug})

    class Meta:
        abstract = True
