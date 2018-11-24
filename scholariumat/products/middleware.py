from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Item


class AddToCartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        item_pk = request.session.get('buy')
        if item_pk and request.user.is_authenticated:
            profile = request.user.profile
            del request.session['buy']
            item = Item.objects.get(pk=item_pk)
            profile.purchase_set.create(item=item, executed=False)
            return HttpResponseRedirect(reverse('products:basket'))
        return self.get_response(request)
