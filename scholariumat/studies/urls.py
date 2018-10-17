from django.urls import path

from .views import StudyView, StudyListView

app_name = 'studies'

urlpatterns = [
    path('', StudyListView.as_view(), name='products'),
    path('produkt/<slug:slug>', StudyView.as_view(), name='product'),
]
