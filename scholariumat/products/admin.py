from django.contrib import admin

from .models import Item, ItemType, Product


class ItemInline(admin.TabularInline):
    model = Item.products.through


class ProductAdmin(admin.ModelAdmin):
    inlines = [ItemInline]


class ItemAdmin(admin.ModelAdmin):
    exclude = ['products']


admin.site.register(Product, ProductAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(ItemType)
