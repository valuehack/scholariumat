from django.contrib import admin

from .models import Article, Bibliography
from framework.admin import PublishAdmin


class ArticleAdmin(PublishAdmin):
    search_fields = ['title']
    list_display = ['title', 'publish_date', 'publish_priority']
    list_filter = ['publish_date']


admin.site.register(Article, ArticleAdmin)
admin.site.register(Bibliography)
