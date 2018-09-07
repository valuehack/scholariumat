from django.urls import path

from .views import homeview

app_name = 'framework'

urlpatterns = [
    path('', homeview, name='home'),
]
