from django import template


register = template.Library()


# TODO: Use request instead of object

# @register.simple_tag
# def get_state(request, item):
#     pass

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
def is_requestable(request, item):
    if request.user.is_authenticated:
        return item.is_requestable(request.user.profile)
    return 0


@register.simple_tag
def is_accessible(request, item):
    if request.user.is_authenticated:
        return item.is_accessible(request.user.profile)
    return 0


@register.simple_tag
def amount_accessible(request, item):
    if request.user.is_authenticated:
        return item.amount_accessible(request.user.profile)
    return 0


@register.simple_tag
def is_purchasable(request, item):
    if request.user.is_authenticated:
        return item.is_purchasable(request.user.profile)
    return False
