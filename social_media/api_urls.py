from django.urls import path, include


urlpatterns = [
    path('', include("post_system.api_urls")),
    path('', include("chat.api_urls")),
    path('', include("notifications.api_urls")),
    path('', include("auth_system.api_urls")),
]