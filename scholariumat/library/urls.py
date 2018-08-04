from django.urls import path

from .views import detail, ZotItemListView

app_name = 'library'

urlpatterns = [
    path('', ZotItemListView.as_view(), name='list'),
    path('kollektion/<slug:collection>', ZotItemListView.as_view(), name='collection'),
    path('objekt/<slug:slug>', detail, name='zot_item'),
]
