from django.contrib import admin
from django.contrib.admin import SimpleListFilter

from .models import Donation, DonationLevel, PaymentMethod


class DonationInline(admin.TabularInline):
    model = Donation
    extra = 0


class LevelFilter(SimpleListFilter):
    """Enable filtering by donation level"""
    title = DonationLevel._meta.verbose_name
    parameter_name = 'level'

    def lookups(self, request, model_admin):
        return [(level.amount, level) for level in DonationLevel.objects.all()]

    def queryset(self, request, queryset):
        return queryset.filter(donation__amount__gte=self.value()) if self.value() else queryset.all()


admin.site.register(DonationLevel)
admin.site.register(PaymentMethod)
