from django import template


register = template.Library()


@register.simple_tag
def number_accessible(request, item):
    return item.number_accessible(request.user.profile)


@register.simple_tag
def is_purchasable(request, item):
    return item.is_purchasable(request.user.profile)
