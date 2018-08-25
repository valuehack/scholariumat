from django.contrib import admin

from .models import ZotItem, Author, Collection
from products.admin import ProductBaseAdmin


class ZotItemAdmin(ProductBaseAdmin):
    raw_id_fields = ['authors']
    search_fields = ['description', 'title']
    list_display = ['title', 'get_authors', 'get_product']
    list_filter = ['published']

    def get_authors(self, obj):  # TODO: Move to deatail view, big list becomes unresponsive.
        return ", ".join([author.__str__() for author in obj.authors.all()])


admin.site.register(Author)
admin.site.register(Collection)
admin.site.register(ZotItem, ZotItemAdmin)
