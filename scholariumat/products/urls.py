from django.urls import path

from .views import BasketView, OrderView

app_name = 'products'

urlpatterns = [
    path('warenkorb', BasketView.as_view(), name='basket'),
    path('bestellungen', OrderView.as_view(), name='orders')
]
