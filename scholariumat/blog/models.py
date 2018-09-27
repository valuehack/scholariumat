import logging
import pypandoc
import re

from django.urls import reverse
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from pyzotero import zotero
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

# from products.behaviours import ProductBase
from framework.behaviours import PublishAble


logger = logging.getLogger(__name__)


class Bibliography(TimeStampedModel):
    slug = models.SlugField(unique=True)
    file = models.FileField()

    class Meta:
        verbose_name = "Bibliographie"
        verbose_name_plural = "Bibliographien"


class Article(TitleSlugDescriptionModel, PublishAble):
    text = models.TextField(blank=True)
    public = models.TextField(editable=False, blank=True)
    public2 = models.TextField(editable=False, blank=True)
    private = models.TextField(editable=False, blank=True)
    references = models.TextField(editable=False, blank=True)

    def markdown_to_html(self):
        if not self.text:
            logger.error(f'{self.title}: No article text found')
            return False

        logger.debug(f'Generating article {self.title}')
        try:
            bib = Bibliography.objects.get(slug='zotero')
        except ObjectDoesNotExist:
            logger.exception('No bibliography found')
            return False

        md = f"---\nbibliography: {bib.file.path}\n---\n\n{self.text}\n\n## Literatur"

        # to html
        html = pypandoc.convert(md, 'html', format='md', filters=['pandoc-citeproc'])

        # # Add class to quotes
        # p = re.compile("<blockquote>")
        # html = p.sub("<blockquote class=\"blockquote\">", html)

        # "--" to "–"
        p = re.compile("--")
        html = p.sub("&ndash;", html)

        # References
        p = re.compile(r'<h2.*Literatur</h2>')
        split = re.split(p, html)
        references = split[1].lstrip() if len(split) > 1 else ""
        if not references:
            logger.debug('No references found')

        # Split hidden text
        p = re.compile(r"<p>&lt;&lt;&lt;</p>")
        split = re.split(p, split[0])
        public = split[0]

        private = split[1].lstrip() if len(split) > 1 else ""
        public2 = split[2].lstrip() if len(split) > 2 else ""

        if not private:
            logger.debug('No hidden part found')

        self.public = public
        self.private = private
        self.public2 = public2
        self.references = references

        logger.debug('Article generation finished')

    @classmethod
    def sync_articles(cls):
        """
        Updates local articles from Zotero. DEPRECATED, NOT IN USE!
        """
        zot = zotero.Zotero(settings.ZOTERO_USER_ID, settings.ZOTERO_LIBRARY_TYPE, settings.ZOTERO_API_KEY)
        articles = zot.everything(zot.items(tag='Scholie', sort='date', direction='desc'))

        print(articles)
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

    def get_absolute_url(self):
        return reverse('blog:article', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        self.markdown_to_html()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta(PublishAble.Meta):
        verbose_name = "Artikel"
        verbose_name_plural = "Artikel"
