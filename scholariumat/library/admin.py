from django.contrib import admin
from django.urls import reverse

from .models import Book, Author, Collection


class BookAdmin(admin.ModelAdmin):
    raw_id_fields = ['authors']
    search_fields = ['description']
    list_display = ['title', 'get_authors', 'get_product']
    list_filter = ['year']

    def get_product(self, obj):
        product = obj.product
        url = reverse('admin:%s_%s_change' % (product._meta.app_label, product._meta.model_name), args=[product.pk])
        return '<a href="%s">%s</a>' % (url, product.__str__())

    def get_authors(self, obj):
        return ", ".join([author.__str__() for author in obj.authors.all()])


admin.site.register(Author)
admin.site.register(Collection)
admin.site.register(Book, BookAdmin)
