from django.urls import path
from .api_views import *


urlpatterns = [
    # Для логіну (Retrofit каже @POST("login/"))
    path('login/', CustomAuthToken.as_view(), name='api_login'),
    
    # Для реєстрації (Retrofit каже @POST("register/"))
    path('register/', api_register, name='api_register'),
    path('user-info/<int:id>/', get_user_detail, name='user_detail'),
]