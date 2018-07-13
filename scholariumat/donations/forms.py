from django import forms

from .models import PaymentMethod, DonationLevel


class PaymentForm(forms.Form):
    level = forms.ModelChoiceField(queryset=DonationLevel.objects.all(), empty_label=None)
    payment_method = forms.ModelChoiceField(queryset=PaymentMethod.objects.all(), empty_label=None)


class ApprovalForm(forms.Form):
    pass
