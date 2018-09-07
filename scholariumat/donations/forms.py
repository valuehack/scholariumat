from django import forms

from .models import PaymentMethod, DonationLevel


class PaymentForm(forms.Form):
    level = forms.ModelChoiceField(label='Stufe', queryset=DonationLevel.objects.all())
    payment_method = forms.ModelChoiceField(label='Zahlungsmethode', queryset=PaymentMethod.objects.all())


class ApprovalForm(forms.Form):
    pass
