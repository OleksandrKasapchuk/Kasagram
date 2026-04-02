from django.urls import path
from .api_views import *


urlpatterns = [
    path('notifications/', NotificationAPIView.as_view(), name='notifications'),
]