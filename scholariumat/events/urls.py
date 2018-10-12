from django.urls import path

from .views import EventView, EventListView, RecordingsView

app_name = 'events'

urlpatterns = [
    path('aufzeichnungen', RecordingsView.as_view(), name='recordings'),
    path('<slug:event_type>', EventListView.as_view(), name='type'),
    path('veranstaltung/<slug:slug>', EventView.as_view(), name='event'),
]
