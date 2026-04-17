from django.contrib import admin
from django.urls import path, include
from . import api_urls
from django.views.generic.base import TemplateView # Додай цей імпорт зверху

urlpatterns = [
    path('admin/', admin.site.urls),
	path('auth/', include('auth_system.urls')),
    path('users/', include("users.urls")),
	path('', include('post_system.urls')),
	path('chat/', include('chat.urls')),
	path('notifications/', include('notifications.urls')),
    path('api/', include(api_urls)),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('sitemap.xml', TemplateView.as_view(template_name="sitemap.xml", content_type="application/xml")),
]