from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from products.models import ProductBase
from framework.behaviours import PublishAble, PermalinkAble
from .utils import markdown_to_html


class Article(ProductBase, PublishAble, PermalinkAble):
    text = models.TextField()
    text_hidden = models.TextField(blank=True)
    text_2 = models.TextField(blank=True)
    references = models.TextField(blank=True)
    priority = models.PositiveSmallIntegerField(default=0)

    def get_absolute_url(self):
        return reverse('blog', [self.slug])

    class Meta:
        verbose_name_plural = "Artikel"
        verbose_name = "Artikel"


class MarkdownArticle(TitleSlugDescriptionModel, TimeStampedModel):
    text = models.TextField()
    priority = models.PositiveSmallIntegerField(default=0)
    article = models.OneToOneField(Article, on_delete=models.SET_NULL, null=True, blank=True)

    def create_article(self):
        text, text_hidden, text_2, references = markdown_to_html(self.text)

        article_kwargs = {
            'art': self.article,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,
            'priority': self.priority,
            'text': text,
            'text_hidden': text_hidden,
            'text_2': text_2,
            'references': references,
        }

        if self.article:
            self.article.update(**article_kwargs)
        elif Article.objects.filter(slug=self.slug).exists():
            raise ValidationError('Artikel-slug existiert bereits.')
        else:
            self.article = Article.objects.create(**article_kwargs)
            self.save()

        print('%s erfolgreich gespeichert.' % self.name)

    def save(self, *args, **kwargs):
        self.create_article()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Markdown Artikel"
        verbose_name = "Markdown Artikel"
