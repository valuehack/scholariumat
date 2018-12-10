from datetime import date

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import OuterRef, Subquery

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
        value = self.value()

        if value:
            donations = Donation.objects.filter(
                profile=OuterRef('pk'), expiration__gte=date.today()).order_by('-amount')
            return queryset.annotate(
                active_donation=Subquery(donations.values('amount')[:1])).filter(active_donation__gte=value)
        return queryset.all()


admin.site.register(DonationLevel)
admin.site.register(PaymentMethod)
