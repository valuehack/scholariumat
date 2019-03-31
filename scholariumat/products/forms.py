from django import forms

from donations.models import PaymentMethod
from .models import Item


class PaymentForm(forms.Form):
    item = forms.ModelChoiceField(
        widget=forms.HiddenInput(), queryset=Item.objects.filter(type__buy_unauthenticated=True))
    payment_method = forms.ModelChoiceField(label='Zahlungsmethode', queryset=PaymentMethod.objects.all())
