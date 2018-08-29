from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from vanilla import ListView
from braces.views import LoginRequiredMixin, MessageMixin

from .models import Item, Purchase


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


class BasketView(LoginRequiredMixin, PurchaseMixin, MessageMixin, ListView):
    template_name = 'products/basket.html'

    def get_queryset(self):
        return Purchase.objects.filter(profile=self.request.user.profile, executed=False)

    def post(self, request, *args, **kwargs):
        if 'buy' in request.POST:
            if request.user.profile.execute_cart():
                self.messages.success('Vielen Dank für Ihre Bestellung.')
                return HttpResponseRedirect(reverse('framework:home'))
            else:
                self.messages.error(
                    f"Ihr Guthaben reicht nicht aus. <a href='{reverse('donations:levels')}'>Erneuern</a> "
                    f"Sie Ihre Unterstützung, um Ihr Guthaben aufzufüllen.")
                return self.get(request, *args, **kwargs)

        if 'remove' in request.POST:
            try:
                purchase = request.user.profile.cart.get(pk=request.POST['remove'])
                purchase.delete()
            except ObjectDoesNotExist:
                pass
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('products:basket')))

        return super().post(request, *args, **kwargs)
