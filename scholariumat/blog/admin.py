from django.contrib import admin

from .models import Article, MarkdownArticle


admin.site.register(Article)
admin.site.register(MarkdownArticle)
