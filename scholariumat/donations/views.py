from django.urls import reverse_lazy, reverse
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.conf import settings
from django.forms import formset_factory, inlineformset_factory

from vanilla import ListView, FormView
from braces.views import MessageMixin

from users.views import UpdateRequiredMixin
from .forms import PaymentForm, ApprovalForm, LevelForm
from .models import DonationLevel, PaymentMethod, Payment


class DonationLevelView(FormView):
    form_class = LevelForm
    template_name = 'donations/donationlevel_form.html'

    def form_valid(self, form):
        level = form.cleaned_data['level']
        return HttpResponseRedirect('{}?amount={}'.format(reverse('donations:payment'), level.amount))


class PaymentView(UpdateRequiredMixin, MessageMixin, FormView):
    """Form to select level and payment method. Can be passed any amount value to initialize the level selection."""
    form_class = PaymentForm
    template_name = 'donations/payment_form.html'

    def get_form(self):
        amount = self.request.GET.get('amount', None)
        if amount:
            level = DonationLevel.get_level_by_amount(amount)
            return self.get_form_class()(initial={'level': level})
        else:
            return super().get_form()

    def form_valid(self, form):
        amount = form.cleaned_data['level'].amount
        method = form.cleaned_data['payment_method']
        payment = Payment.objects.create(amount=amount, method=method)
        if payment.init():
            # TODO: Delete old payments
            # TODO: Create new user -> auto login?
            self.request.session.pop('updated', None)  # TODO:delete
            return HttpResponseRedirect(payment.approval_url)
        else:
            self.messages.error(settings.MESSAGES_UNEXPECTED_ERROR)
            return self.form_invalid(form)


class ApprovalView(MessageMixin, FormView):
    form_class = ApprovalForm
    template_name = 'donations/approval_form.html'
    success_url = reverse_lazy('framework:home')

    def dispatch(self, *args, **kwargs):
        if not Payment.objects.filter(slug=self.kwargs.get('slug')):
            return HttpResponseNotFound()
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        payment = Payment.objects.get(slug=self.kwargs.get('slug'))
        if payment.execute(self.request):
            self.messages.info('Vielen Dank für Ihre Unterstützung')
            return super().form_valid(form)
        else:
            self.messages.error(settings.MESSAGES_UNEXPECTED_ERROR)
            return HttpResponseRedirect(reverse('donations:payment'))
            

        # post_data = self.request.POST
        # for key, value in post_data.items():
        #     if value == 'success':
        #         method = PaymentMethod.objects.get(slug=key)
        #         if method.execute_payment(self.request):
        #             messages.success(self.request, 'Vielen Dank für Ihre Unterstützung')
        # messages.error(self.request, settings.MESSAGES_UNEXPECTED_ERROR)
        # return super(ApprovalForm, self).form_valid(form)
