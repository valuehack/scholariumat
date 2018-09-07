from django.urls import path

from .views import BasketView, PurchaseView

app_name = 'products'

urlpatterns = [
    path('warenkorb', BasketView.as_view(), name='basket'),
    path('bestellungen', PurchaseView.as_view(), name='purchases')
]
