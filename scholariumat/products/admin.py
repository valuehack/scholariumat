from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Item, ItemType, Product, Purchase, FileAttachment


class ProductBaseAdmin(admin.ModelAdmin):
    search_fields = ['description', 'title']
    list_display = ['title', 'get_product']

    def get_product(self, obj):
        product = obj.product
        url = reverse('admin:%s_%s_change' % (product._meta.app_label, product._meta.model_name), args=[product.pk])
        return format_html('<a href="%s">%s</a>' % (url, product.__str__()))


class ItemInline(admin.TabularInline):
    model = Item
    show_change_link = True


class ProductAdmin(admin.ModelAdmin):
    inlines = [ItemInline]

    def get_search_fields(self, request):
        """Searches realted one_to_one fields (actual products)"""
        return [f'{related.name}__title' for related in self.model._meta.get_fields() if related.one_to_one]


class PurchaseAdmin(admin.ModelAdmin):
    raw_id_fields = ['profile', 'item']
    readonly_fields = ['executed']


class AttachmentInline(admin.TabularInline):
    model = FileAttachment


class ItemAdmin(admin.ModelAdmin):
    inlines = [AttachmentInline]
    raw_id_fields = ['product']
    list_display = ['type', 'price', 'product']


class AttachmentAdmin(admin.ModelAdmin):
    raw_id_fields = ['item']


admin.site.register(Product, ProductAdmin)
admin.site.register(ItemType)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(Item, ItemAdmin)
