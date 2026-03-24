from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Реєстрація (наша кастомна в'юшка)
    path('register/', views.RegisterView.as_view(), name='register'),

    # Логін та Логаут (вбудовані, просто вказуємо шаблон)
    path('login/', auth_views.LoginView.as_view(
        template_name='form.html',
        extra_context={'title': 'Login'}
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Зміна пароля (Django сам перевірить старий пароль і хешує новий)
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='form.html',
        success_url='/', # куди кидати після зміни
        extra_context={'title': 'Change Password'}
    ), name='password_change'),

    # Профіль та редагування
    path('user-info/<int:pk>/', views.UserDetailView.as_view(), name='user-info'),
    path('edit-user/', views.UserUpdateView.as_view(), name='edit-user'),
]