from django.contrib import messages
from django.views.generic import ListView, UpdateView
# from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy


from .forms import UpdateEmailForm
from .models import DonationLevel, Profile


class ProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ['title', 'name', 'organization', 'street', 'postcode', 'country']
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        messages.info(self.request, 'Änderungen gespeichert.')
        return super().form_valid(form)


class UpdateEmailView(LoginRequiredMixin, UpdateView):
    form_class = UpdateEmailForm
    template_name = 'users/email_form.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        return self.request.user


class LevelView(ListView):
    model = DonationLevel


def donate_view(request):
    pass
