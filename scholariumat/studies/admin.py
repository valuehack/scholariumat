from django.contrib import admin

from products.admin import ProductBaseAdmin
from .models import StudyProduct


admin.site.register(StudyProduct, ProductBaseAdmin)
