from django.urls import path

from .views import BasketView, PurchaseView, HistoryView, PaymentView, ApprovalView, DownloadView

app_name = 'products'

urlpatterns = [
    path('warenkorb', BasketView.as_view(), name='basket'),
    path('bestellungen', PurchaseView.as_view(), name='purchases'),
    path('historie', HistoryView.as_view(), name='purchase_history'),
    path('zahlung', PaymentView.as_view(), name='payment'),
    path('bestaetigung/<slug:slug>', ApprovalView.as_view(), name='approve'),

    path('miseskreis82236442', DownloadView.as_view(), name="miseskreis")
]
