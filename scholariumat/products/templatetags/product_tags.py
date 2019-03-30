from django import template


register = template.Library()


@register.simple_tag
def item_status(request, item):
    return item.get_status(request.user)


@register.simple_tag
def item_price(request, item):
    return item.get_price(request.user)


@register.simple_tag
def items_accessible(request, product):
    if request.user.is_authenticated:
        return product.items_accessible(request.user.profile)
    return None


@register.simple_tag
def any_attachments_accessible(request, product):
    if request.user.is_authenticated:
        return product.any_attachments_accessible(request.user.profile)
    return None


@register.simple_tag
def is_accessible(request, item):
    if request.user.is_authenticated:
        return item.is_accessible(request.user)
    return 0
