from django import forms
from django.contrib.auth import get_user_model


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
