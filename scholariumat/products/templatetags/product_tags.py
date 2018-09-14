from django import template


register = template.Library()


@register.simple_tag
def items_accessible(request, product):
    return request.user.profile.items_accessible(product)


@register.simple_tag
def amount_accessible(request, item):
    return request.user.profile.amount_accessible(item)


@register.simple_tag
def is_purchasable(request, item):
    return item.is_purchasable(request.user.profile)
