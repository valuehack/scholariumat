from django.urls import path

from .views import ZotItemDetailView, ZotItemListView

app_name = 'library'

urlpatterns = [
    path('', ZotItemListView.as_view(), name='list'),
    path('kollektion/<slug:collection>', ZotItemListView.as_view(), name='collection'),
    path('objekt/<slug:slug>', ZotItemDetailView.as_view(), name='zotitem'),
]
