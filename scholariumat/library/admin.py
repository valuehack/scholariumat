from django.contrib import admin

from .models import Book, Author, Collection
from products.admin import ProductBaseAdmin


class BookAdmin(ProductBaseAdmin):
    raw_id_fields = ['authors']
    search_fields = ['description']
    list_display = ['title', 'get_authors', 'get_product']
    list_filter = ['year']

    def get_authors(self, obj):
        return ", ".join([author.__str__() for author in obj.authors.all()])


admin.site.register(Author)
admin.site.register(Collection)
admin.site.register(Book, BookAdmin)
