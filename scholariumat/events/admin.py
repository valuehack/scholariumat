from django.contrib import admin

from products.admin import ProductBaseAdmin
from .models import Event, EventType, Livestream


class LivestreamAdmin(admin.ModelAdmin):
    raw_id_fields = ['item']


admin.site.register(Event, ProductBaseAdmin)
admin.site.register(EventType)
admin.site.register(Livestream, LivestreamAdmin)
