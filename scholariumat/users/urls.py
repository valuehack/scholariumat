from django.urls import path

from .views import ProfileView, LevelView, UpdateEmailView, update_profile_user_view

app_name = 'users'

urlpatterns = [
    path('profil/', ProfileView.as_view(), name='profile'),
    path('stufen/', LevelView.as_view(), name='levels'),
    path('spende/', update_profile_user_view, name='donate'),
    path('email/', UpdateEmailView.as_view(), name='update_email'),
]
