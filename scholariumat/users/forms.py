import logging

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
# from django.utils.crypto import get_random_string

from .models import Profile


logger = logging.getLogger(__name__)


class UserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['email']

    def save(self, commit=True):
        """Creates user with randomized password and sends out email with pw reset link."""
        if commit:
            # PW reset mail won't be send when password is None
            user = super().save(commit=False)
            user.set_password(get_user_model().objects.make_random_password())
            user.save()

            # Send mail with password reset link
            email = self.cleaned_data['email']
            reset_form = PasswordResetForm({'email': email})
            if not reset_form.is_valid():
                errors = reset_form.errors
                logger.error(f'Sending activation mail to {email} failed: {errors}')
            reset_form.save(
                subject_template_name='registration/user_creation_subject.txt',
                email_template_name='registration/user_creation_email.html',
                from_email=settings.DEFAULT_FROM_EMAIL)
            logger.info(f'Activation email send to {email}')
        else:
            user = super().save(commit=False)
        return user


class UpdateEmailForm(UserForm):
    password = forms.CharField(label='Bestätigen Sie Ihr Passwort', widget=forms.PasswordInput)

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.instance.check_password(password):
            raise forms.ValidationError('Invalid password')
        return password


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['title', 'name', 'organization', 'street', 'postcode', 'country']
