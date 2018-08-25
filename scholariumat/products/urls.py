from django.urls import path

from .views import BasketView

app_name = 'products'

urlpatterns = [
    path('warenkorb', BasketView.as_view(), name='basket'),
]
