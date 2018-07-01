from django.urls import path

from .views import list, detail, collection

app_name = 'library'

urlpatterns = [
    path('', list),
    path('kollektion/<slug:slug>', collection, name='collection'),
    path('objekt/<slug:slug>', detail, name='zot_item'),
]
