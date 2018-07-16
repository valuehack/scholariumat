from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.contrib import messages

from braces.views import LoginRequiredMixin, FormValidMessageMixin, AnonymousRequiredMixin, MessageMixin
from vanilla import UpdateView, CreateView, GenericView, FormView, TemplateView, RedirectView
from authtools.forms import UserCreationForm

from .forms import UpdateEmailForm, ProfileForm, UserForm


class RedirectMixin:
    """Mixin for looking for next parameter in GET"""
    def get_success_url(self):
        return self.request.GET.get('next') or super().get_success_url()


class UpdateRequiredMixin:
    """
    Saves request parameters to session and returns view to create/update profile.
    If session contains 'updated' key, return current view with saved parameters.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('updated'):
            # Save params to session
            request.session['get_params'] = request.GET.dict()
            request.session['post_params'] = request.POST.dict()

            redirect_url = reverse('users:update') if request.user.is_authenticated else reverse('users:create')
            return HttpResponseRedirect('{}?next={}'.format(redirect_url, request.path_info))

        # Pop url params and add to GET/POST
        get_params = request.session.pop('get_params', {})
        post_params = request.session.pop('post_params', {})
        request.GET = request.GET.copy()
        request.GET.update(get_params)
        request.POST = request.POST.copy()
        request.POST.update(post_params)
        return super().dispatch(request, *args, **kwargs)


class CreateUserView(AnonymousRequiredMixin, RedirectMixin, MessageMixin, CreateView):
    form_class = UserForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['profile_form'] = ProfileForm(self.request.POST)
        else:
            context['profile_form'] = ProfileForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        profile_form = context['profile_form']
        if profile_form.is_valid():
            # Create User with Profile
            self.object = form.save()
            profile = profile_form.save(commit=False)
            profile.user = self.object
            profile.save()
            self.messages.info('Profil gespeichert')
            self.request.session['updated'] = True
            return HttpResponseRedirect(self.success_url)
        else:
            return self.form_invalid(form)


# class CreateUserView(FormValidMessageMixin, CreateView):
#     form_class = UserForm
#     # model = get_user_model()
#     # fields = ['email']
#     template_name = 'users/user_form.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         if self.request.POST:
#             context['profile_formset'] = ProfileFormSet(self.request.POST)
#         else:
#             context['profile_formset'] = ProfileFormSet()
#         return context
#
#     def form_valid(self, form):
#         context = self.get_context_data()
#         formset = context['profile_formset']
#         if formset.is_valid():
#             self.object = form.save(commit=False)
#             formset.instance = self.object
#             formset.save()
#             return HttpResponseRedirect(self.success_url)
#         else:
#             return self.render_to_response(self.get_context_data(form=form))

class ProfileView(LoginRequiredMixin, FormValidMessageMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'users/profile.html'
    form_valid_message = 'Profil gespeichert'
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        return self.request.user.profile

    def form_valid(self, form):
        self.request.session['updated'] = True
        return super().form_valid(form)


class UpdateProfileView(RedirectMixin, ProfileView):
    template_name = 'users/profile_form.html'


class UpdateEmailView(LoginRequiredMixin, FormValidMessageMixin, UpdateView):
    form_class = UpdateEmailForm
    template_name = 'users/email_form.html'
    success_url = reverse_lazy('users:profile')
    form_valid_message = 'Email-Adresse gespeichert'

    def get_object(self):
        return self.request.user
