from vanilla import DetailView, ListView

from products.views import PurchaseMixin, DownloadMixin
from .models import StudyProduct


class StudyListView(ListView):
    model = StudyProduct
    paginate_by = 5
    template_name = 'products/product_list.html'


class StudyView(PurchaseMixin, DownloadMixin, DetailView):
    model = StudyProduct
    lookup_field = 'slug'
    template_name = 'products/product_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact'] = True
        return context
