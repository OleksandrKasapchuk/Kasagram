from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from . import api_urls


def robots_txt(request):
    # Дозволяємо Гуглу ходити до нашого API без перешкод
    lines = [
        "User-agent: *",
        "Allow: /api/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


urlpatterns = [
    path('admin/', admin.site.urls),
	path('auth/', include('auth_system.urls')),
    path('users/', include("users.urls")),
	path('', include('post_system.urls')),
	path('chat/', include('chat.urls')),
	path('notifications/', include('notifications.urls')),
    path('api/', include(api_urls)),
    path("robots.txt", robots_txt, name="robots_txt"),
]