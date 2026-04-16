from django.urls import path
import post_system.views as post_views

urlpatterns = [
	path('', post_views.IndexView.as_view(), name='index'),
	path('post_details/<int:pk>/', post_views.PostDetailView.as_view(), name='post-details'),
	path('add_post/', post_views.PostCreateView.as_view(), name='add_post'),
	path('update_post/<int:pk>', post_views.PostUpdateView.as_view(), name='update_post'),
	path('delete_post/<int:pk>', post_views.PostDeleteView.as_view(), name='delete_post'),
	path('update-comment/<int:pk>/', post_views.UpdateCommentView.as_view(), name='update-comment'),
]

app_name = 'post' 