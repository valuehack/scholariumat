from datetime import date

from django.db import models


class PublishedManager(models.Manager):

    def published(self, **kwargs):
        return self.filter(publish_date__lte=date.today(), **kwargs)

    def unpublished(self, **kwargs):
        return self.exclude(publish_date__lte=date.today(), **kwargs)
