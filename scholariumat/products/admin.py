from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Item, ItemType, Product, Purchase


class ProductBaseAdmin(admin.ModelAdmin):

    def get_product(self, obj):
        product = obj.product
        url = reverse('admin:%s_%s_change' % (product._meta.app_label, product._meta.model_name), args=[product.pk])
        return format_html('<a href="%s">%s</a>' % (url, product.__str__()))


class ItemInline(admin.TabularInline):
    model = Item


class ProductAdmin(admin.ModelAdmin):
    inlines = [ItemInline]


class PurchaseAdmin(admin.ModelAdmin):
    raw_id_fields = ['profile', 'item']
    readonly_fields = ['executed']


class ItemAdmin(admin.ModelAdmin):
    raw_id_fields = ['product']
    list_display = ['type', 'price', 'product']


admin.site.register(Product, ProductAdmin)
admin.site.register(ItemType)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(Item, ItemAdmin)
