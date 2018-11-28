from django.db.models import Q
from django.conf import settings

from vanilla import ListView, DetailView
from braces.views import LoginRequiredMixin
from pyzotero import zotero

from .models import ZotItem, Collection
from framework.views import CompatibleOrderableListMixin
from products.views import PurchaseMixin, DownloadMixin


class ZotItemListView(LoginRequiredMixin, CompatibleOrderableListMixin, ListView):
    model = ZotItem
    paginate_by = 10
    orderable_columns = ['title', 'published', 'authors']
    orderable_columns_default = 'published'
    ordering_default = 'desc'

    def dispatch(self, *args, **kwargs):
        collection_slug = self.kwargs.get('collection')
        self.collection = Collection.objects.get(slug=collection_slug) if collection_slug else None
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['children'] = Collection.objects.filter(parent=self.collection)
        if self.collection:
            context['collection'] = self.collection
            context['parents'] = self.collection.get_parents()

        return context

    def get_queryset(self):
        search = self.request.GET.get('search')
        if search:
            items = ZotItem.objects.filter(Q(title__icontains=search) | Q(authors__name__icontains=search))
            items = items.distinct()
        else:
            # Only filter for collection if no search
            items = ZotItem.objects.filter(collection=self.collection)

        return self.get_ordered_queryset(queryset=items)


class ZotItemDetailView(LoginRequiredMixin, PurchaseMixin, DownloadMixin, DetailView):
    model = ZotItem
    lookup_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zot = zotero.Zotero(settings.ZOTERO_USER_ID, settings.ZOTERO_LIBRARY_TYPE, settings.ZOTERO_API_KEY)
        context['api_object'] = zot.item(self.object.slug)
        return context
