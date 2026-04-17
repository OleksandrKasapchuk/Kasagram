from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-info'),
    path('edit-user/', views.UserUpdateView.as_view(), name='edit-user'),
    path('followers/<int:pk>', views.FollowerView.as_view(), name='get-followers'),
    path('following/<int:pk>', views.FollowingView.as_view(), name='get-following'),
]