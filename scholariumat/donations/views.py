import logging

from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from vanilla import FormView, DetailView, ListView
from braces.views import MessageMixin

from users.views import UpdateOrCreateRequiredMixin
from .forms import PaymentForm, ApprovalForm
from .models import DonationLevel, Donation


logger = logging.getLogger(__name__)


class DonationView(DetailView):
    model = Donation

    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse_lazy('donations:levels'))
        return super().dispatch(*args, **kwargs)

    def get_object(self):
        donation = self.request.user.profile.donation
        if not donation:
            raise Http404('Keine aktive Unterstützung')
        return donation


class DonationLevelView(ListView):
    """Overview of available donation levels"""
    model = DonationLevel
    template_name = 'donations/donationlevel_list.html'


class PaymentView(UpdateOrCreateRequiredMixin, MessageMixin, FormView):
    """Form to select level and payment method. Can be passed any amount value to initialize the level selection."""
    form_class = PaymentForm
    template_name = 'donations/payment_form.html'

    def get_form(self, data=None, files=None, **kwargs):
        amount = self.request.GET.get('amount', None)
        if amount:
            level = DonationLevel.get_level_by_amount(amount)
            return super().get_form(data, files, initial={'level': level}, **kwargs)
        else:
            return super().get_form(data, files, **kwargs)

    def form_valid(self, form):
        amount = form.cleaned_data['level'].amount
        method = form.cleaned_data['payment_method']
        profile = self.get_profile()
        profile.clean_donations()  # Clean up old initiated donations
        donation = profile.donation_set.create(amount=amount, method=method)
        logger.debug(f'Created donation {donation}')
        if donation.init():
            logger.debug(f'Initiated donation {donation}. Redirecting to {donation.approval_url}')
            return HttpResponseRedirect(donation.approval_url)
        else:
            logger.error(f'Failed to intiate donation {donation}')
            self.messages.error(settings.MESSAGE_UNEXPECTED_ERROR)
            return self.form_invalid(form)


class ApprovalView(MessageMixin, FormView):
    """Executes the referenced payment. Approvement button is only shown if payment method required it."""
    form_class = ApprovalForm
    template_name = 'donations/approval_form.html'
    success_url = reverse_lazy('users:profile')

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""
        kwargs['donation'] = self.donation
        return super().get_context_data(**kwargs)

    def dispatch(self, *args, **kwargs):
        try:
            self.donation = Donation.objects.get(slug=self.kwargs.get('slug'))
        except ObjectDoesNotExist:
            return HttpResponseNotFound()  # Cancel if non-existent payment is referenced

        if self.donation.executed:  # Cancel if payment already executed
            self.messages.info('Zahlung bereits erfolgreich durchgeführt.')
            return HttpResponseRedirect(self.get_success_url())

        if not self.donation.method.local_approval:
            return self.form_valid(self.get_form())
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        self.donation.execute(self.request)
        if self.donation.executed:
            self.messages.info('Vielen Dank für Ihre Unterstützung')
            return HttpResponseRedirect(self.get_success_url())
        else:
            self.messages.error(settings.MESSAGE_UNEXPECTED_ERROR)
            return HttpResponseRedirect(reverse('donations:levels'))
