from django.contrib import messages
from django.conf import settings

from .models import Item


class PurchaseMixin():
    """Purchases or requests Item"""

    def post(self, request, *args, **kwargs):
        if 'requested_item' in request.POST:
            item = Item.objects.get(pk=request.POST['requested_item'])
            if item.available:
                item.add_to_cart(request.user.profile)
                messages.info(request, settings.MESSAGE_CART_ADDED)
            else:
                item.request(request.user.profile)
                messages.info(request, settings.MESSAGE_REQUEST_SEND)
        if hasattr(super(), 'post'):
            return super().post(request, *args, **kwargs)
        else:
            # Might be used for Classview without post function
            return self.get(request, *args, **kwargs)
