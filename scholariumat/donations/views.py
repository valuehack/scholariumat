from django.urls import reverse_lazy, reverse
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.conf import settings
from django.forms import formset_factory, inlineformset_factory

from vanilla import ListView, FormView

from users.views import UpdateRequiredMixin
from .forms import PaymentForm, ApprovalForm
from .models import DonationLevel, PaymentMethod


class LevelView(ListView):
    model = DonationLevel


class PaymentView(UpdateRequiredMixin, FormView):
    form_class = PaymentForm
    template_name = 'donations/payment_form.html'

    # def post(self, request, *args, **kwargs):
    #     TODO: retrieve amount

    def form_valid(self, form):
        # context = self.get_context_data()
        # amount = context.get('amount') or DonationLevel.get_lowest_amount()
        amount = form.cleaned_data['level'].amount
        method = form.cleaned_data['payment_method']
        return HttpResponseRedirect(method.get_approval_url(amount))


# def payment_view(request):
#     """Combines User, Profile and Paymentmethod forms."""
#     if request.user.is_authenticated():
#         formset = formset_factory(ProfileForm)
#         formset.instance = request.user.profile
#     else:
#         formset = inlineformset_factory(UserForm, ProfileForm)
#     payment_form = PaymentForm()
# 
#     if request.method == 'POST':
#         if formset.is_valid():
#             instances = formset.save(commit=False)
# 
#             payment_form = PaymentForm(request.POST)
#             user = user_form.save()
#             profile = profile_form.save(commit=False)
#             profile.user = user
#             profile.save()
#             messages.info('Profil gespeichert')
#             method = payment_form.cleaned_data['payment_method']
#             approval_url = method.create_payment(request.POST.get('amount', 75))
#             if approval_url:
#                 # request.session['payment_id'] = payment.id  # TODO: necessary?
#                 # return payment.url
#                 return approval_url
#             else:
#                 messages.error(request, settings.MESSAGES_UNEXPECTED_ERROR)
#                 return reverse('users:payment')
# 
#     context = {
#         'forms': formset,
#     }
#     return render(request, 'donations/payment_form_test.html', context)


# def payment_view(request):
#     """Combines User, Profile and Paymentmethod forms."""
#     if request.user.is_authenticated():
#         profile_form = ProfileForm(instance=request.user.profile)
#     else:
#         user_form = UserForm()
#         profile_form = ProfileForm()
#     payment_form = PaymentForm()
# 
#     if request.method == 'POST':
#         user_form = UserForm(request.POST)
#         profile_form = ProfileForm(request.POST)
#         payment_form = PaymentForm(request.POST)
#         if profile_form.is_valid() and user_form.is_valid() and payment_form.is_valid():
#             user = user_form.save()
#             profile = profile_form.save(commit=False)
#             profile.user = user
#             profile.save()
#             messages.info('Profil gespeichert')
#             method = payment_form.cleaned_data['payment_method']
#             approval_url = method.create_payment(request.POST.get('amount', 75))
#             if approval_url:
#                 # request.session['payment_id'] = payment.id  # TODO: necessary?
#                 # return payment.url
#                 return approval_url
#             else:
#                 messages.error(request, settings.MESSAGES_UNEXPECTED_ERROR)
#                 return reverse('users:donate')
# 
#     context = {
#         'profile_form': profile_form,
#         'user_form': user_form,
#         'payment_form': payment_form
#     }
#     return render(request, 'donations/payment_form.html', context)


class ApprovalView(FormView):
    form_class = ApprovalForm
    template_name = 'donations/approval_form.html'
    success_url = reverse_lazy('framework:home')

    def form_valid(self, form):
        post_data = self.request.POST
        for key, value in post_data.items():
            if value == 'success':
                method = PaymentMethod.objects.get(slug=key)
                if method.execute_payment(self.request):
                    messages.success(self.request, 'Vielen Dank für Ihre Unterstützung')
        messages.error(self.request, settings.MESSAGES_UNEXPECTED_ERROR)
        return super(ApprovalForm, self).form_valid(form)
