from django.urls import path

from .views import UpdateProfileView, UpdateEmailView, CreateUserView, ProfileView

app_name = 'users'

urlpatterns = [
    path('', ProfileView.as_view(), name='profile'),
    path('neu/', CreateUserView.as_view(), name='create'),
    path('update/', UpdateProfileView.as_view(), name='update'),
    path('email/', UpdateEmailView.as_view(), name='update_email'),
]
