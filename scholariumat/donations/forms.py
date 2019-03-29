from django import forms

from .models import PaymentMethod, DonationLevel


class PaymentForm(forms.Form):
    amount = forms.IntegerField(widget=forms.HiddenInput(), initial=DonationLevel.get_lowest_amount())
    payment_method = forms.ModelChoiceField(label='Zahlungsmethode', queryset=PaymentMethod.objects.all())


class ApprovalForm(forms.Form):
    pass
