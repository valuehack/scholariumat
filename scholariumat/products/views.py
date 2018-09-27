from datetime import date

from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import mail_managers

from vanilla import ListView, TemplateView
from braces.views import LoginRequiredMixin, MessageMixin

from .models import Item, Purchase


class PurchaseMixin():
    """Adds functionality to request or add to basket"""

    def post(self, request, *args, **kwargs):
        if 'requested_item' in request.POST:
            item = Item.objects.get(pk=request.POST['requested_item'])
            if item.available:
                if item.add_to_cart(request.user.profile):
                    messages.info(request, settings.MESSAGE_CART_ADDED)
            else:
                item.request(request.user.profile)
                messages.info(request, settings.MESSAGE_REQUEST_SEND)
        if hasattr(super(), 'post'):
            return super().post(request, *args, **kwargs)
        else:
            # Might be used for Classview without post function
            return self.get(request, *args, **kwargs)


class DownloadMixin():
    """Adds functionality to download an attachment"""

    def post(self, request, *args, **kwargs):
        if hasattr(super(), 'post'):
            response = super().post(request, *args, **kwargs)
        else:
            response = self.get(request, *args, **kwargs)

        if 'download' in request.POST:
            item = Item.objects.get(pk=request.POST['download'])
            if item.amount_accessible(request.user.profile):
                attachment = item.attachments[int(request.POST.get('id', '0'))]
                try:
                    download = attachment.get()
                    if download:
                        return download
                    raise FileNotFoundError()
                except FileNotFoundError:
                    messages.error(request, settings.MESSAGE_NOT_FOUND)
                    edit_url = reverse('admin:products_item_change', args=[item.pk])
                    mail_managers(
                        f'Fehlende Datei: {item.product} als {attachment}',
                        f'Das Item kann unter folgender URL editiert werden: {settings.DEFAULT_DOMAIN}{edit_url}')

            else:
                return HttpResponse(status=405)

        return response


class BasketView(LoginRequiredMixin, PurchaseMixin, MessageMixin, ListView):
    template_name = 'products/basket.html'

    def get_queryset(self):
        return Purchase.objects.filter(profile=self.request.user.profile, executed=False)

    def post(self, request, *args, **kwargs):
        if 'buy' in request.POST:
            if request.user.profile.execute_cart():
                self.messages.success('Vielen Dank für Ihre Bestellung.')
                return HttpResponseRedirect(reverse('products:purchases'))
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


class PurchaseView(LoginRequiredMixin, DownloadMixin, TemplateView):
    template_name = 'products/purchases.html'

    def get_context_data(self, **kwargs):
        purchases = self.request.user.profile.purchases
        products = self.request.user.profile.products_bought

        context = {
            'purchases': purchases,
        }

        events = products.filter(item__type__slug__in=['livestream', 'attendence'])
        context['future_events'] = events.filter(event__date__gte=date.today())
        context['past_events'] = events.filter(event__date__lt=date.today())

        context['digital_content'] = products.filter(zotitem__isnull=False, item__amount__isnull=True)
        return context
