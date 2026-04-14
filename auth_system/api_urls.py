from django.urls import path
from .api_views import *


urlpatterns = [
    path('login/', CustomAuthToken.as_view(), name='api_login'),
    path('register/', api_register, name='api_register'),
    path('user-info/<int:pk>/', UserDetailAPIView.as_view(), name='user_detail'),
    path('toggle-follow/<int:pk>/', ToggleFollowAPIView.as_view()),
    path('me/', MeAPIView.as_view())
]