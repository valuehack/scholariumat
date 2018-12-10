from django.urls import path

from .views import HomeView, FaqView, ContactView, IljaView

app_name = 'framework'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('fragen', FaqView.as_view(), name='faq'),
    path('Kontakt', ContactView.as_view(), name='contact')
    path('iljatest', IljaView.as_view(), name='ilja')
]
