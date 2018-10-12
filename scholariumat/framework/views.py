from django.urls import reverse
from django.http import HttpResponseRedirect

from braces.views import OrderableListMixin, LoginRequiredMixin
from vanilla import TemplateView


class CompatibleOrderableListMixin(OrderableListMixin):
    """
    OrderableListMixin compatible with different GET params.
    (webstack-django-sort uses sort/dir instead of order_by/ordering)
    """

    order_by_param = 'sort'
    direction_param = 'dir'

    def get_ordered_queryset(self, queryset=None):
        """
        Augments ``QuerySet`` with order_by statement if possible
        :param QuerySet queryset: ``QuerySet`` to ``order_by``
        :return: QuerySet
        """
        get_order_by = self.request.GET.get(self.order_by_param)

        if get_order_by in self.get_orderable_columns():
            order_by = get_order_by
        else:
            order_by = self.get_orderable_columns_default()

        self.order_by = order_by
        self.ordering = self.get_ordering_default()

        if order_by and self.request.GET.get(
                self.direction_param, self.ordering) == "desc":
            order_by = "-" + order_by
        self.ordering = self.request.GET.get(self.direction_param, self.ordering)

        return queryset.order_by(order_by)


class HomeView(TemplateView):
    template_name = 'framework/home.html'


class FaqView(TemplateView):
    template_name = 'framework/faq.html'


class ContactView(TemplateView):
    template_name = 'framework/contact.html'
