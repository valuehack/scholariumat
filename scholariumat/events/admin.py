from django.contrib import admin

from products.admin import ProductBaseAdmin
from .models import Event, EventType, Livestream


class LivestreamAdmin(admin.ModelAdmin):
    raw_id_fields = ['item']


class EventAdmin(ProductBaseAdmin):
    list_display = ProductBaseAdmin.list_display + ['type', 'date']
    list_filter = ['type', 'date']


admin.site.register(Event, EventAdmin)
admin.site.register(EventType)
admin.site.register(Livestream, LivestreamAdmin)
