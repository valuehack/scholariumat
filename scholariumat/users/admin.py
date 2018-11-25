import csv

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from authtools.admin import UserAdmin

from donations.admin import DonationInline, LevelFilter
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'level', 'balance', 'expiration']
    search_fields = ['user__email', 'name']
    raw_id_fields = ['user']
    list_filter = [LevelFilter]
    inlines = [DonationInline]
    actions = ['generate_csv']

    def generate_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="profiles.csv"'
        writer = csv.writer(response, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(
            ['Anrede', 'Vorname', 'Nachname', 'Email', 'Firma', 'Addresse', 'Land', 'Stufe', 'Ablaufdatum', 'Guthaben'])
        for profile in queryset:
            writer.writerow([
                profile.title,
                profile.first_name,
                profile.last_name,
                profile.user.email,
                profile.organization,
                profile.address,
                profile.country,
                profile.level,
                profile.expiration,
                profile.amount
            ])

        return response

    generate_csv.short_description = 'CSV Dokument generieren'


admin.site.register(Profile, ProfileAdmin)
admin.site.register(get_user_model(), UserAdmin)
