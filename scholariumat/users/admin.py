from django.contrib import admin
from django.contrib.auth import get_user_model

from authtools.admin import UserAdmin

from donations.admin import DonationInline, LevelFilter
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'level', 'balance', 'expiration']
    search_fields = ['user__email', 'name']
    raw_id_fields = ['user']
    list_filter = [LevelFilter]
    inlines = [DonationInline]


admin.site.register(Profile, ProfileAdmin)
admin.site.register(get_user_model(), UserAdmin)
