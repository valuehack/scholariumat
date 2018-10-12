from django.urls import path

from .views import EventView, EventListView

app_name = 'events'

urlpatterns = [
    path('<slug:event_type>', EventListView.as_view(), name='type'),
    path('veranstaltung/<slug:slug>', EventView.as_view(), name='event'),
]
