from django.urls import path

from .views import EventView, EventListView, RecordingsView, AttendancesView

app_name = 'events'

urlpatterns = [
    path('aufzeichnungen', RecordingsView.as_view(), name='recordings'),
    path('salons', EventListView.as_view(event_type='salon'), name='salons'),
    path('seminare', EventListView.as_view(event_type='seminar'), name='seminars'),
    path('vortrag', EventListView.as_view(event_type='vortrag'), name='lectures'),
    path('veranstaltung/<slug:slug>', EventView.as_view(), name='event'),
    path('veranstaltung/<slug:slug>/teilnehmer', AttendancesView.as_view(), name='attendances'),
]
