from django.urls import path

from .views import list, detail

app_name = 'library'

urlpatterns = [
    path('', list, name='list'),
    path('kollektion/<slug:collection>', list, name='collection'),
    path('objekt/<slug:slug>', detail, name='zot_item'),
]
