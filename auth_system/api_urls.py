from django.urls import path
from .api_views import *


urlpatterns = [
    path('login/', CustomAuthToken.as_view(), name='api_login'),
    path('register/', api_register, name='api_register'),
    path('change-password/', api_change_password, name='api_change_password'),
    path('edit-profile/', api_edit_profile, name='api_edit_profile'),
]