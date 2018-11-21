from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def content_accessible(request, article):
    if request.user.is_authenticated:
        return request.user.profile.amount >= settings.ARTICLE_ACCESSIBLE_AT
    return False
