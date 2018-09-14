from django.views.generic import DetailView, ListView

from braces.views import LoginRequiredMixin

from .models import Article


class ArticleDetailView(LoginRequiredMixin, DetailView):
    model = Article


class ArticleListView(ListView):
    model = Article
