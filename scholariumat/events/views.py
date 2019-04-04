from datetime import date
from vanilla import DetailView, ListView
from braces.views import LoginRequiredMixin, StaffuserRequiredMixin

from django.db.models import Q
from django.http import Http404

from products.views import PurchaseMixin, DownloadMixin
from .models import Event, EventType


class EventListView(PurchaseMixin, DownloadMixin, ListView):
    model = Event
    paginate_by = 10
    event_type = None

    def dispatch(self, *args, **kwargs):
        event_type = self.kwargs.get('event_type') or self.event_type
        if event_type:
            try:
                self.event_type = EventType.objects.get(Q(section_title=event_type) | Q(slug=event_type))
            except EventType.DoesNotExist:
                raise Http404()
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        return Event.objects.published().filter(
            type=self.event_type, date__lt=date.today()).order_by('-date').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = self.event_type
        context['future_events'] = Event.objects.published().filter(
            type=self.event_type, date__gte=date.today()).order_by('date')
        return context


class EventView(PurchaseMixin, DownloadMixin, DetailView):
    model = Event
    lookup_field = 'slug'


class AttendancesView(StaffuserRequiredMixin, DetailView):
    template_name = 'events/attendances.html'
    model = Event
    lookup_field = 'slug'


class RecordingsView(LoginRequiredMixin, PurchaseMixin, DownloadMixin, ListView):
    model = Event
    paginate_by = 10
    template_name = 'events/recording_list.html'

    def get_queryset(self):
        return Event.objects.published().filter(date__lt=date.today()).order_by('-date').distinct()
