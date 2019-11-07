import logging
from datetime import date

from django.contrib import messages
from django.conf import settings
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import mail_managers
from django.contrib.auth import login

from vanilla import ListView, TemplateView, FormView
from braces.views import LoginRequiredMixin, MessageMixin

from events.models import Event
from library.models import ZotItem
from donations.models import DonationLevel
from donations.forms import ApprovalForm
from users.views import UpdateOrCreateRequiredMixin
from .models import Item, Purchase, Payment
from .forms import PaymentForm


logger = logging.getLogger(__name__)


class PurchaseMixin():
    """Adds functionality to request or add to basket"""

    def post(self, request, *args, **kwargs):
        if 'requested_item' in request.POST:
            item = Item.objects.get(pk=request.POST['requested_item'])
            if item.available:
                if 'buy_directly' in request.POST:
                    if not item.type.requires_donation:
                        amount = item.get_price()
                        return HttpResponseRedirect(f"{reverse('products:payment')}?item={item.pk}")

                if request.user.is_authenticated:
                    if item.add_to_cart(request.user.profile):
                        messages.info(request, settings.MESSAGE_CART_ADDED)
                else:
                    if item.type.requires_donation:
                        request.session['buy'] = item.pk
                        amount = DonationLevel.get_necessary_level(item.get_price()).amount
                        return HttpResponseRedirect(f"{reverse('donations:payment')}?amount={amount}")
                    else:
                        amount = item.get_price()
                        return HttpResponseRedirect(f"{reverse('products:payment')}?item={item.pk}")
            else:
                item.request(request.user)
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
            if item.is_accessible(request.user):
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
        purchases = self.request.user.profile.purchases.order_by('-date')
        products = self.request.user.profile.products_bought

        context = {
            'purchases': purchases,
        }

        events = Event.objects.filter(product__in=products)
        # events = products.filter(item__type__slug__in=['livestream', 'attendence'])
        context['future_events'] = {event: purchases.filter(item__product=event.product) for
                                    event in events.filter(date__gte=date.today())}
        context['past_events'] = {event: purchases.filter(item__product=event.product) for
                                  event in events.filter(date__lt=date.today())}

        # context['digital_content'] = products.filter(zotitem__isnull=False, item__amount__isnull=True)
        digital_product = {product: purchases.filter(item__product=product) for
                           product in products.filter(item__amount__isnull=True)}
        context['digital_content'] = {item: purchases.filter(item__product=item.product) for
                                      item in ZotItem.objects.filter(product__in=digital_product)}
        return context


class PaymentView(UpdateOrCreateRequiredMixin, MessageMixin, FormView):
    form_class = PaymentForm
    template_name = 'donations/payment_form.html'

    def get_form(self, data=None, files=None, **kwargs):
        item = self.request.GET.get('item', None)
        if item:
            return super().get_form(data, files, initial={'item': item}, **kwargs)
        else:
            return super().get_form(data, files, **kwargs)

    def form_valid(self, form):
        item = form.cleaned_data['item']
        if not item:
            return HttpResponseRedirect(reverse('donations:levels'))
        method = form.cleaned_data['payment_method']
        profile = self.get_profile()
        profile.clean_payments()
        purchase = Purchase.objects.create(item=item, profile=profile)
        payment = Payment.objects.create(profile=profile, purchase=purchase, method=method, amount=item.get_price())
        logger.debug(f'Created payment {payment}')

        if payment.init():
            logger.debug(f'Initiated payment {payment}. Redirecting to {payment.approval_url}')
            return HttpResponseRedirect(payment.approval_url)
        else:
            logger.error(f'Failed to intiate payment {payment}')
            self.messages.error(settings.MESSAGE_UNEXPECTED_ERROR)
            return self.form_invalid(form)


class ApprovalView(MessageMixin, FormView):
    """Executes the referenced payment. Approvement button is only shown if payment method required it."""
    form_class = ApprovalForm
    template_name = 'products/approval_form.html'
    success_url = reverse_lazy('products:purchases')

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""
        kwargs['payment'] = self.payment
        return super().get_context_data(**kwargs)

    def dispatch(self, *args, **kwargs):
        try:
            self.payment = Payment.objects.get(slug=self.kwargs.get('slug'))
        except ObjectDoesNotExist:
            return HttpResponseNotFound()  # Cancel if non-existent payment is referenced

        if self.payment.executed:  # Cancel if payment already executed
            self.messages.info('Zahlung bereits erfolgreich durchgeführt.')
            return HttpResponseRedirect(self.get_success_url())

        if not self.payment.method.local_approval:
            return self.form_valid(self.get_form())
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        self.payment.execute(self.request)
        if self.payment.executed:
            self.messages.info('Vielen Dank für Ihre Bestellung')
            if not self.request.user.is_authenticated:
                login(self.request, self.payment.profile.user)
            return HttpResponseRedirect(self.get_success_url())
        else:
            self.messages.error(settings.MESSAGE_UNEXPECTED_ERROR)
            return HttpResponseRedirect(reverse('framework:home'))


class HistoryView(LoginRequiredMixin, ListView):
    template_name = 'products/purchase_history.html'

    def get_queryset(self):
        return self.request.user.profile.purchases.order_by('-date')


class DownloadView(TemplateView):
    template_name = 'mises_songs.html'
