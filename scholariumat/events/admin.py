from django.contrib import admin
from django.urls import reverse

from products.admin import ProductBaseAdmin
from .models import Event, EventType, Livestream


class LivestreamAdmin(admin.ModelAdmin):
    change_form_template = "admin/livestream_changeform.html"
    raw_id_fields = ['product']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        event = self.get_object(request, object_id).product.event
        extra_context['event'] = reverse(
            'admin:%s_%s_change' % (event._meta.app_label, event._meta.model_name), args=[event.pk])
        return super().change_view(request, object_id, form_url='', extra_context=extra_context)


class EventAdmin(ProductBaseAdmin):
    list_display = ProductBaseAdmin.list_display + ['type', 'date']
    list_filter = ['type', 'date']


admin.site.register(Event, EventAdmin)
admin.site.register(EventType)
admin.site.register(Livestream, LivestreamAdmin)
