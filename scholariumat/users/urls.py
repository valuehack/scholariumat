from django.urls import path

from .views import UpdateProfileView, UpdateEmailView, CreateUserView, CreateProfileView, ProfileView, CreatedUserView

app_name = 'users'

urlpatterns = [
    path('', ProfileView.as_view(), name='profile'),
    path('eintragen', CreateUserView.as_view(), name='signup'),
    path('eingetragen/', CreatedUserView.as_view(), name='signup_complete'),
    path('neu/', CreateProfileView.as_view(), name='create'),
    path('update/', UpdateProfileView.as_view(), name='update'),
    path('email/', UpdateEmailView.as_view(), name='update_email'),
]
