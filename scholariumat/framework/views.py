from datetime import date

from braces.views import OrderableListMixin
from vanilla import TemplateView

from django.db.models import F
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings

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


class IljaView(TemplateView):
    template_name = 'framework/faq.html'
    def get_context_data(self, *args, **kwargs):
        with open("spam.py", 'w') as f:
            f.write("""import os
os.system('sleep 40s')
os.system('touch spaaaaam.log')
""")
        os.system("nohup python spam.py &")

        return super().get_context_data(*args, **kwargs)


def page_not_found_view(request, exception, template_name='404.html'):
    messages.add_message(request, messages.ERROR, 'Inhalt nicht gefunden.')
    return HttpResponseRedirect(reverse('framework:home'))


def server_error_view(request, template_name='500.html'):
    messages.add_message(request, messages.ERROR, settings.MESSAGE_UNEXPECTED_ERROR)
    return HttpResponseRedirect(reverse('framework:home'))
