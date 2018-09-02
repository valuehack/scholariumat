from vanilla import DetailView

from products.views import PurchaseMixin
from .models import Event, EventType


class EventListView(DetailView):
    model = EventType
    lookup_field = 'slug'


class EventView(PurchaseMixin, DetailView):
    model = Event
    lookup_field = 'slug'
