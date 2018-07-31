import logging

from django import forms
from django.contrib.auth import get_user_model

from .models import Profile


logger = logging.getLogger(__name__)


class UserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['email']

    def save(self, commit=True):
        """Sends out email with pw reset link if user is created."""
        user = super().save(commit=commit)
        if commit:
            user.send_activation_mail()
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
        fields = ['title', 'name', 'organization', 'street', 'postcode', 'city', 'country']
        
        _field_class = {
            'title': 'three wide'
        }
        
        # Layout used by django-semanticui
        layout = [
            ("Two Fields",
                ("Field", "title"),
                ("Field", "name")),
            ("Field", "organization"),
            ("Two Fields",
                ("Field", "street"),
                ("Field", "postcode")),
        ]
