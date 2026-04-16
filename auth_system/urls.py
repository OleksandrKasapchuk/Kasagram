from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),

    path('login/', auth_views.LoginView.as_view(
        template_name='form.html',extra_context={'title': 'Login'}), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Зміна пароля (Django сам перевірить старий пароль і хешує новий)
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='form.html',
        success_url='/', # куди кидати після зміни
        extra_context={'title': 'Change Password'}
    ), name='password_change'),
]