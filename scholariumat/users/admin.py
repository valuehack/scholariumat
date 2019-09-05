import csv
from datetime import date

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.db.models import OuterRef, Subquery

from authtools.admin import UserAdmin

from donations.models import Donation
from donations.admin import DonationInline, LevelFilter, ExpirationFilter, InterestedFilter
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'level', 'balance', 'expiration']
    search_fields = ['user__email', 'first_name', 'last_name']
    raw_id_fields = ['user']
    list_filter = [LevelFilter, ExpirationFilter, InterestedFilter]
    inlines = [DonationInline]
    actions = ['generate_csv_full', 'generate_csv_emails_only']

    def generate_csv_emails_only(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="profiles.csv"'
        writer = csv.writer(response, quoting=csv.QUOTE_MINIMAL)
        writer.writerows(queryset.values_list('user__email'))
        return response

    generate_csv_emails_only.short_description = 'CSV Dokument generieren (Nur Emails)'

    def generate_csv_full(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="profiles.csv"'
        writer = csv.writer(response, quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            'Anrede', 'Vorname', 'Nachname', 'Email', 'Firma', 'Straße', 'PLZ',
            'Stadt', 'Land', 'Stufe', 'Ablaufdatum', 'Guthaben'])

        active_donations = Donation.objects.filter(
            profile=OuterRef('pk'), expiration__gte=date.today()).order_by('-amount')
        latest_donations = Donation.objects.filter(profile=OuterRef('pk')).order_by('-expiration')
        queryset = queryset.annotate(
            active_donation=Subquery(active_donations.values('amount')[:1]),
            expiration_date=Subquery(latest_donations.values('expiration')[:1]))

        writer.writerows(queryset.values_list(
            'title',
            'first_name',
            'last_name',
            'user__email',
            'organization',
            'street',
            'postcode',
            'city',
            'country',
            'active_donation',
            'expiration_date',
            'balance'))

        return response

    generate_csv_full.short_description = 'CSV Dokument generieren'


admin.site.register(Profile, ProfileAdmin)
admin.site.register(get_user_model(), UserAdmin)
