from django.views.generic import DetailView, ListView

from braces.views import LoginRequiredMixin

from .models import Article


class ArticleDetailView(LoginRequiredMixin, DetailView):
    model = Article


class ArticleListView(ListView):
    model = Article
    paginate_by = 5
    queryset = Article.objects.published()
    template_name = 'blog/article_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff:
            context['unpublished'] = Article.objects.unpublished()
        return context
