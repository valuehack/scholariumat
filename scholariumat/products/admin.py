try:
    from s3upload.widgets import S3UploadWidget
except ModuleNotFoundError:
    pass

from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.db import models
from django.conf import settings

from .models import Item, ItemType, Product, Purchase, FileAttachment, AttachmentType


class ProductBaseAdmin(admin.ModelAdmin):
    search_fields = ['description', 'title']
    list_display = ['title']
    change_form_template = "admin/productbase_changeform.html"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        product = self.get_object(request, object_id).product
        extra_context['product'] = reverse(
            'admin:%s_%s_change' % (product._meta.app_label, product._meta.model_name), args=[product.pk])
        return super().change_view(request, object_id, form_url='', extra_context=extra_context)


class ItemInline(admin.TabularInline):
    model = Item
    raw_id_fields = ['files']
    show_change_link = True


class ProductAdmin(admin.ModelAdmin):
    inlines = [ItemInline]
    change_form_template = "admin/product_changeform.html"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        product_type = self.get_object(request, object_id).type
        extra_context['type'] = reverse(
            'admin:%s_%s_change' % (product_type._meta.app_label, product_type._meta.model_name),
            args=[product_type.pk])
        return super().change_view(request, object_id, form_url='', extra_context=extra_context)

    def get_search_fields(self, request):
        """Searches realted one_to_one fields (actual products)"""
        return [f'{related.name}__title' for related in self.model._meta.get_fields() if related.one_to_one]


class PurchaseAdmin(admin.ModelAdmin):
    raw_id_fields = ['profile', 'item']
    readonly_fields = ['executed']


class ItemAdmin(admin.ModelAdmin):
    change_form_template = "admin/item_changeform.html"
    raw_id_fields = ['product', 'files']
    list_display = ['type', 'price', 'product']

    def response_change(self, request, obj):
        if "_inform-users" in request.POST:
            obj.inform_users()
            self.message_user(request, "Die Anfragen wurden beantwortet.")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


class AttachmentAdmin(admin.ModelAdmin):
    if 's3upload' in settings.INSTALLED_APPS:
        formfield_overrides = {
            models.FileField: {'widget': S3UploadWidget(dest='default')},
        }


admin.site.register(Product, ProductAdmin)
admin.site.register(ItemType)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(FileAttachment, AttachmentAdmin)
admin.site.register(AttachmentType)
