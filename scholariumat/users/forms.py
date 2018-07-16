import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm

from .models import Profile


logger = logging.getLogger(__name__)


class UserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['email']

    def clean(self):
        super().clean()
        reset_form = PasswordResetForm({
            'email': self.cleaned_data['email'],
            'subject_template_name': 'registration/account_creation_subject.txt',
            'email_template_name': 'registration/account_creation_email.html'})
        if not reset_form.is_valid():
            logger.error('Sending activation mail failed:' + reset_form.errors)
        reset_form.save()


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
