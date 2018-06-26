from django.urls import path

from .views import ArticleListView, ArticleDetailView

app_name = "blog"

urlpatterns = [
    path("", view=ArticleListView.as_view(), name="list"),
    path("<slug:slug>", view=ArticleDetailView.as_view(), name="article",),
]
