from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

# from vanilla import ListView
# from braces.view import LoginRequiredMixin

from .models import ZotItem, Collection
from .forms import SearchForm


@login_required
def list(request, collection=None):

    sort = request.GET.get('sort')
    search = request.GET.get('search')
    page = request.GET.get('seite')
    # types = request.GET.getlist('type')

    context = {}

    # Filter for search term
    if search:
        items = ZotItem.objects.filter(Q(title__icontains=search) | Q(authors__name__icontains=search))
        items = items.distinct()
    else:
        # Only filter for collection if no search
        collection = Collection.objects.get(slug=collection) if collection else None
        items = ZotItem.objects.filter(collection=collection)
        context['children'] = Collection.objects.filter(parent=collection)
        if collection:
            context['collection'] = collection
            context['parents'] = collection.get_parents()

    context['searchform'] = SearchForm
    # context['filterform'] = FilterForm
    # filtered = True if types else False

    # if filtered and not buecher:
    #     messages.info(request, 'Kein Buch gefunden, dass den Filterkriterien entspricht.')

    # Table sort
    if sort:
        sort = "-" + sort if request.GET.get('dir', '') == 'desc' else sort
        items = items.order_by(sort)
    else:
        items = items.order_by('-published')

    # Pagination
    paginator = Paginator(items, 10)
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)

    context['paginator'] = paginator
    context['zotitems'] = items

    return render(request, 'library/zotitem_list.html', context)


def detail(request, slug):
    pass
