from vanilla import DetailView

from products.views import PurchaseMixin, DownloadMixin
from .models import Event, EventType


class EventListView(DetailView):
    model = EventType
    lookup_field = 'slug'


class EventView(PurchaseMixin, DownloadMixin, DetailView):
    model = Event
    lookup_field = 'slug'
