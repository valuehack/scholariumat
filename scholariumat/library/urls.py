from django.urls import path

from .views import list, detail, collection

app_name = 'library'

urlpatterns = [
    path('', list),
    path('kollektion/<slug:slug>', collection, name='collection'),
    path('buch/<slug:slug>', detail, name='book'),
]
