from django.db import models
from django.urls import reverse

from django_extensions.db.models import TimeStampedModel

from products.models import ProductBase, Purchase
from framework.behaviours import CommentAble, PermalinkAble


class Collection(PermalinkAble):
    name = models.CharField(max_length=200)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Kollektion'
        verbose_name_plural = 'Kollektionen'


class Author(models.Model):
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)

    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autoren'


class Book(ProductBase, PermalinkAble):
    authors = models.ManyToManyField(Author)
    year = models.DateField(blank=True, null=True)
    collection = models.ManyToManyField(Collection)

    def get_lendings(self):
        return self.lending_set.filter(returned__isnull=True)

    def get_lendings_possible(self):
        return self.product_set.get(name='Leihe').amount - len(self.get_lendings())

    def __str__(self):
        return '%s (%s)' % (self.title, ', '.join([author.__str__() for author in self.authors.all()]))

    class Meta:
        verbose_name = 'Buch'
        verbose_name_plural = 'Bücher'


class Lending(TimeStampedModel, CommentAble):
    purchase = models.OneToOneField(Purchase, on_delete=models.CASCADE)
    returned = models.DateField(blank=True, null=True)
    charged = models.DateField(blank=True, null=True)

    def __str__(self):
        return '%s: %s' % (self.profile.__str__(), self.purchase.__str__())

    class Meta:
        verbose_name = 'Leihe'
        verbose_name_plural = 'Leihen'


class Booklet(ProductBase, PermalinkAble):
    image = models.ImageField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse('library:booklet', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = "Büchlein"
        verbose_name_plural = "Büchlein"
