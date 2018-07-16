from django.contrib import admin

from .models import Menu, MenuItem, MenuSubItem


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 0


class MenuAdmin(admin.ModelAdmin):
    inlines = [MenuItemInline]


admin.site.register(Menu, MenuAdmin)
