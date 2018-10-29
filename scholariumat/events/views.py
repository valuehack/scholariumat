from datetime import date
from vanilla import DetailView, ListView
from braces.views import LoginRequiredMixin, StaffuserRequiredMixin

from django.db.models import Q

from products.views import PurchaseMixin, DownloadMixin
from .models import Event, EventType


class EventListView(ListView):
    model = Event
    paginate_by = 5
    event_type = None

    def dispatch(self, *args, **kwargs):
        event_type = self.kwargs.get('event_type')
        if event_type:
            self.event_type = EventType.objects.get(Q(section_title=event_type) | Q(slug=event_type))
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(type=self.event_type, date__gte=date.today(), publish_date__lte=date.today()).order_by('date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.event_type:
            context['section_title'] = self.event_type.section_title or self.event_type.title
        else:
            context['section_title'] = 'Veranstaltungen'
        return context


class EventView(PurchaseMixin, DownloadMixin, DetailView):
    model = Event
    lookup_field = 'slug'


class AttendancesView(StaffuserRequiredMixin, DetailView):
    template_name = 'events/attendances.html'
    model = Event
    lookup_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['purchases'] = self.get_object().product.item_set.get(type__slug='attendance').purchase_set.filter(executed=True)
        context['total'] = sum([purchase.amount for purchase in context['purchases']])
        return context


class RecordingsView(LoginRequiredMixin, PurchaseMixin, DownloadMixin, ListView):
    model = Event
    paginate_by = 10
    template_name = 'events/recording_list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(date__lt=date.today()).order_by('-date').distinct()
