from datetime import date

from braces.views import OrderableListMixin
from vanilla import TemplateView

from django.db.models import F

from events.models import Event
from blog.models import Article


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
            self.ordering = self.request.GET.get(self.direction_param, self.ordering)
            return queryset.order_by(F(order_by).desc(nulls_last=True))
        else:
            self.ordering = self.request.GET.get(self.direction_param, self.ordering)
            return queryset.order_by(F(order_by).asc(nulls_last=True))


class HomeView(TemplateView):
    template_name = 'framework/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['events'] = Event.objects.published().filter(date__gte=date.today()).order_by('date')[:4]
            articles = Article.objects.published()[:4]
            if articles:
                article_list = list(articles)
                context['feature'] = article_list.pop(0)
                context['articles'] = article_list
        return context


class FaqView(TemplateView):
    template_name = 'framework/faq.html'


class ContactView(TemplateView):
    template_name = 'framework/contact.html'
