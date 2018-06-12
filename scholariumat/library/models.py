from django.db import models
from django.core.exceptions import ObjectDoesNotExist

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


class Book(ProductBase):
    slug = models.CharField(max_length=50, unique=True)
    authors = models.ManyToManyField(Author)
    year = models.DateField(blank=True, null=True)
    collection = models.ManyToManyField(Collection)

    @property
    def lendings_active(self):
        return self.lending_set.filter(returned__isnull=True)

    @property
    def lendings_possible(self):
        try:
            return self.product.item_set.get(type__title='Leihe').amount - len(self.lendings_active)
        except ObjectDoesNotExist:
            return None

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


class Booklet(ProductBase):
    image = models.ImageField(null=True, blank=True)

    class Meta:
        verbose_name = "Büchlein"
        verbose_name_plural = "Büchlein"
