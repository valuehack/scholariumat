from products.behaviours import ProductBase

from django.urls import reverse


class StudyProduct(ProductBase):
    """Products concerned with the studies"""

    def get_absolute_url(self):
        return reverse('studies:product', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = "Studienprodukt"
        verbose_name_plural = "Studienprodukte"
