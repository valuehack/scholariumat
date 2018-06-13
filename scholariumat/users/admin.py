from django.contrib import admin
# from django.contrib.auth import get_user_model

# from authtools.admin import NamedUserAdmin
from .models import Profile, Donation


# class UserAdmin(NamedUserAdmin):
#     list_display = ("username", "name", "is_superuser")
#     search_fields = ["name"]


class DonationInline(admin.TabularInline):
    model = Donation
    min_num = 1


class ProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ['user']
    inlines = [DonationInline]


# admin.site.unregister(get_user_model())
# admin.site.register(get_user_model(), UserAdmin)
admin.site.register(Profile, ProfileAdmin)
