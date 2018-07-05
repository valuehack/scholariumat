from django.urls import path

from .views import ProfileView, LevelView, donate_view, UpdateEmailView

app_name = 'users'

urlpatterns = [
    path('profil/', ProfileView.as_view(), name='profile'),
    path('stufen/', LevelView.as_view(), name='levels'),
    path('spende/', donate_view, name='donate'),
    path('email/', UpdateEmailView.as_view(), name='update_email'),
]
