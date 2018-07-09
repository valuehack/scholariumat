from django.urls import reverse_lazy, reverse
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings

from braces.views import LoginRequiredMixin, FormValidMessageMixin
from vanilla import ListView, UpdateView, FormView

from .forms import UpdateEmailForm, ProfileForm, UserForm, PaymentForm, ApprovalForm
from .models import DonationLevel, Donation


class UpdateProfileView(LoginRequiredMixin, FormValidMessageMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'users/profile_form.html'
    form_valid_message = 'Profil gespeichert'

    def get_object(self):
        return self.request.user.profile

    def get_success_url(self):
        return self.kwargs['next'] or super(UpdateProfileView, self).get_success_url()


class ProfileView(UpdateProfileView):
    success_url = reverse_lazy('users:profile')
    template_name = 'users/profile.html'


class UpdateEmailView(LoginRequiredMixin, FormValidMessageMixin, UpdateView):
    form_class = UpdateEmailForm
    template_name = 'users/email_form.html'
    success_url = reverse_lazy('users:profile')
    form_valid_message = 'Email-Adresse gespeichert'

    def get_object(self):
        return self.request.user


class LevelView(ListView):
    model = DonationLevel


def payment_view(request):
    """Combines User, Profile and Paymentmethod forms."""
    profile_form = ProfileForm()
    user_form = UserForm()
    payment_form = PaymentForm()

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST)
        user_form = UserForm(request.POST)
        payment_form = PaymentForm(request.POST)
        if profile_form.is_valid() and user_form.is_valid() and payment_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.info('Profil gespeichert')
            method = payment_form.cleaned_data['payment_method']
            payment = method.get_payment(request.POST.get('amount', 75))
            if payment.url:
                request.session['payment_id'] = payment.id
                return payment.url
            else:
                messages.error(request, settings.MESSAGES_UNEXPECTED_ERROR)
                return reverse('users:donate')

    context = {
        'profile_form': profile_form,
        'user_form': user_form,
        'payment_form': payment_form
    }
    return render(request, 'users/payment_form.html', context)


class ApprovalView(FormView):
    form_class = ApprovalForm
    success_url = reverse_lazy('framework:home')

    def form_valid(self, form):
        donation = Donation.objects.get(payment_id=self.request.session['payment_id'])
        donation.pay()
        messages.success(self.request, 'Vielen Dank für Ihre Unterstützung')
