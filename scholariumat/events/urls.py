from django.urls import path

from .views import EventView, EventListView

app_name = 'events'

urlpatterns = [
    path('<slug:slug>', EventListView.as_view(), name='type'),
    path('<slug:slug>', EventView.as_view(), name='event'),
]
