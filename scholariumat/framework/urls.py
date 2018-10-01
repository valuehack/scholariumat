from django.urls import path

from .views import homeview, FaqView, ContactView

app_name = 'framework'

urlpatterns = [
    path('', homeview, name='home'),
    path('fragen', FaqView.as_view(), name='faq'),
    path('Kontakt', ContactView.as_view(), name='contact')
]
