import logging

from django.db import models
from django.conf import settings

from pyzotero import zotero

from products.models import ProductBase
from framework.behaviours import PublishAble

logger = logging.getLogger(__name__)


class Article(ProductBase, PublishAble):
    text = models.TextField()

    @classmethod
    def sync_articles(cls):
        '''
        Updates local articles from Zotero.
        '''
        zot = zotero.Zotero(settings.ZOTERO_USER_ID, settings.ZOTERO_LIBRARY_TYPE, settings.ZOTERO_API_KEY)
        articles = zot.everything(zot.items(tag='Scholie', sort='date', direction='desc'))

        # Get all articles
        for article in articles:
            title = article['data']['title']
            key = article['key']
            notes = [child['data']['note'] for child in zot.children(key) if child['data']['itemType'] == 'note']
            try:
                html_text = next(iter(notes))  # Retrieve html formatted text from first note
            except StopIteration:
                logger.warning('Article {} is empty! Skipping...'.format(title))
                continue  # Skip empty articles

            obj, created = cls.objects.update_or_create(slug=key, defaults={'title': title, 'text': html_text})
            return obj

        # Clean up deleted articles.
        for local_article in cls.objects.all():
            if local_article.slug not in [article['key'] for article in articles]:
                local_article.delete()
            children = zot.children(local_article.slug)
            return children

    class Meta:
        verbose_name = "Artikel"
        verbose_name_plural = "Artikel"
