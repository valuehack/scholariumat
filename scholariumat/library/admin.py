from django.contrib import admin

from .models import ZotItem, Author, Collection, ZotAttachment, Lending
from products.admin import ProductBaseAdmin, AttachmentAdmin


class ZotItemAdmin(ProductBaseAdmin):
    raw_id_fields = ['authors']
    search_fields = ['description', 'title']
    list_display = ['title', 'get_authors', 'published']
    list_filter = ['published']

    def get_authors(self, obj):  # TODO: Move to detail view, big list becomes unresponsive.
        return ", ".join([author.__str__() for author in obj.authors.all()])


class AuthorAdmin(admin.ModelAdmin):
    search_fields = ['name']


class CollectionAdmin(admin.ModelAdmin):
    search_fields = ['title']
    list_display = ['title', 'parent']
    list_filter = ['parent']


class LendingAdmin(admin.ModelAdmin):
    list_display = ['get_profile', 'get_zotitem', 'returned', 'charged']

    def get_profile(self, obj):
        return obj.purchase.profile

    def get_zotitem(self, obj):
        return obj.purchase.item.product.zotitem


admin.site.register(Author, AuthorAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(ZotItem, ZotItemAdmin)
# admin.site.register(ZotAttachment, AttachmentAdmin)
# admin.site.register(Lending, LendingAdmin)
