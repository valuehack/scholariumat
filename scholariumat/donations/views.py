import logging

from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.conf import settings

from vanilla import FormView
from braces.views import MessageMixin

from users.views import UpdateOrCreateRequiredMixin
from .forms import PaymentForm, ApprovalForm, LevelForm
from .models import DonationLevel, Donation


logger = logging.getLogger(__name__)


class DonationLevelView(FormView):
    form_class = LevelForm
    template_name = 'donations/donationlevel_form.html'

    def form_valid(self, form):
        level = form.cleaned_data['level']
        return HttpResponseRedirect('{}?amount={}'.format(reverse('donations:payment'), level.amount))


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
        if donation.init():
            logger.debug(f'Created and initiated donation {donation}')
            return HttpResponseRedirect(donation.approval_url)
        else:
            self.messages.error(settings.MESSAGES_UNEXPECTED_ERROR)
            return self.form_invalid(form)


class ApprovalView(MessageMixin, FormView):
    form_class = ApprovalForm
    template_name = 'donations/approval_form.html'
    success_url = reverse_lazy('users:profile')

    def dispatch(self, *args, **kwargs):
        if not Donation.objects.filter(slug=self.kwargs.get('slug')):
            return HttpResponseNotFound()
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        donation = Donation.objects.get(slug=self.kwargs.get('slug'))
        if donation.execute(self.request):
            self.messages.info('Vielen Dank für Ihre Unterstützung')
            return HttpResponseRedirect(self.get_success_url())
        else:
            self.messages.error(settings.MESSAGES_UNEXPECTED_ERROR)
            return HttpResponseRedirect(reverse('donations:levels'))
