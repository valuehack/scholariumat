from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model

from authtools.admin import UserAdmin

from .models import Profile, Donation, DonationLevel, PaymentMethod


class DonationInline(admin.TabularInline):
    model = Donation


class LevelFilter(SimpleListFilter):
    """Enable filtering by donation level"""
    title = DonationLevel._meta.verbose_name
    parameter_name = 'level'

    def lookups(self, request, model_admin):
        return [(level.amount, level) for level in DonationLevel.objects.all()]

    def queryset(self, request, queryset):
        return queryset.filter(donation__level__amount=self.value()) if self.value() else queryset.all()


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'level', 'balance', 'expiration']
    search_fields = ['user__email', 'user__name']
    raw_id_fields = ['user']
    list_filter = [LevelFilter]
    inlines = [DonationInline]

admin.site.register(Profile, ProfileAdmin)
admin.site.register(DonationLevel)
admin.site.register(PaymentMethod)
admin.site.register(get_user_model(), UserAdmin)
