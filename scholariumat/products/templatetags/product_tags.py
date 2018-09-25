from django import template


register = template.Library()


@register.simple_tag
def items_accessible(request, product):
    return product.items_accessible(request.user.profile)


@register.simple_tag
def attachments_accessible(request, product):
    return product.attachments_accessible(request.user.profile)


@register.simple_tag
def amount_accessible(request, item):
    return item.amount_accessible(request.user.profile)


@register.simple_tag
def is_purchasable(request, item):
    return item.is_purchasable(request.user.profile)
