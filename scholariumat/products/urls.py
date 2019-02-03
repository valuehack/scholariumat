from django.urls import path

from .views import BasketView, PurchaseView, HistoryView

app_name = 'products'

urlpatterns = [
    path('warenkorb', BasketView.as_view(), name='basket'),
    path('bestellungen', PurchaseView.as_view(), name='purchases'),
    path('historie', HistoryView.as_view(), name='purchase_history')
]
