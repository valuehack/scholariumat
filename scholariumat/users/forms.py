import logging
from captcha.fields import ReCaptchaField

from django import forms
from django.contrib.auth import get_user_model

from .models import Profile


logger = logging.getLogger(__name__)


class UserForm(forms.ModelForm):
    captcha = ReCaptchaField(attrs={'_no_label': True, '_no_errors': True})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()

        return email

    class Meta:
        model = get_user_model()
        fields = ['email']

    def save(self, commit=True, profile_kwargs={}):
        """Sends out email with pw reset link if user is created."""
        user = super().save(commit=commit)
        if commit:
            Profile.objects.create(user=user, **profile_kwargs)
            logger.info(f'Created profile for {user}')
            user.send_activation_mail()
        return user


class UpdateEmailForm(forms.ModelForm):
    password = forms.CharField(label='Bestätigen Sie Ihr Passwort', widget=forms.PasswordInput)

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.instance.check_password(password):
            raise forms.ValidationError('Invalid password')
        return password

    class Meta:
        model = get_user_model()
        fields = ['email']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['title', 'first_name', 'last_name', 'organization', 'street', 'postcode', 'city', 'country']

        _field_class = {
            'title': 'three wide'
        }

        # Layout used by django-semanticui
        layout = [
            ("Three Fields",
                ("Field", "title"),
                ("Field", "first_name"),
                ("Field", "last_name")),
            ("Field", "organization"),
            ("Field", "street"),
            ("Two Fields",
                ("Field", "postcode"),
                ("Field", "city")),
        ]
