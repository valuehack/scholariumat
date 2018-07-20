from django.urls import path

from .views import DonationLevelView, ApprovalView, PaymentView

app_name = 'donations'

urlpatterns = [
    path('', DonationLevelView.as_view(), name='levels'),
    path('zahlung', PaymentView.as_view(), name='payment'),
    path('bestaetigung/<slug:slug>', ApprovalView.as_view(), name='approve'),
]
