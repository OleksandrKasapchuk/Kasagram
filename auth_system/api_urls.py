from django.urls import path
from .api_views import *


urlpatterns = [
    path('login/', CustomAuthToken.as_view(), name='api_login'),
    path('register/', api_register, name='api_register'),
]