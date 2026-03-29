from django.urls import path
from post_system.api_views import *
from rest_framework.authtoken import views as auth_views


urlpatterns = [
    path('token-auth/', auth_views.obtain_auth_token),
]