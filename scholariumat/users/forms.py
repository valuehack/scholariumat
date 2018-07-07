from django import forms
from django.contrib.auth import get_user_model

from .models import Profile, PaymentMethod


class UserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['email']


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


class PaymentForm(forms.Form):
    payment_method = forms.ModelChoiceField(queryset=PaymentMethod.objects.all())
