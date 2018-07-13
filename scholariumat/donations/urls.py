from django.urls import path

from .views import LevelView, ApprovalView, PaymentView

app_name = 'donations'

urlpatterns = [
    path('', LevelView.as_view(), name='levels'),
    path('zahlung', PaymentView.as_view(), name='payment'),
    path('bestaetigung/', ApprovalView.as_view(), name='approve'),
]
