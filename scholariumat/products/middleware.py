from .models import Item
from .views import BasketView


class AddToCartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        item_pk = request.session.get('buy')
        if item_pk and request.user.is_authenticated:
            profile = request.user.profile
            # try:
            item = Item.objects.get(pk=item_pk)
            profile.purchase_set.create(item=item, executed=False)
            return BasketView.as_view()(request)
            # except Item.ObjectNotFound:
            #     pass
        return self.get_response(request)
