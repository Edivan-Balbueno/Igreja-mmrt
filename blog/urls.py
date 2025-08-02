# blog/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"), # <--- Nova Home
    path('index', views.index, name="index"), # <--- Remova ou comente esta linha
    path('videos/', views.videos, name="videos"), # <--- Nova URL para vídeos
    path('perfil', views.perfil, name="perfil"),
    path('quemsomos', views.quemsomos, name="quemsomos"),
    path('contato', views.contato, name="contato"),
    path('mundokids', views.mundokids, name="mundokids"),
    path('addcomment/<int:id>', views.addcomment, name='addcomment'),
    path('blog_admin/comments/', views.manage_comments, name='manage_comments'),
    path('blog_admin/', views.blog_admin_dashboard, name='blog_admin_dashboard'),
    #path('blog_admin/approve-comment/<int:comment_id>/', views.approve_comment, name='approve_comment'),
    path('blog_admin/create-admin/', views.create_blog_admin, name='create_blog_admin'),
    path('blog_admin/post/create/', views.create_post, name='create_post'), # Descomente se já tiver a view
    path('blog_admin/post/edit/<int:post_id>/', views.edit_post, name='edit_post'), # Descomente se já tiver a view
    path('blog_admin/post/delete/<int:post_id>/', views.delete_post, name='delete_post'),
    #path('blog_admin/comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('blog_admin/carousel_images/', views.carousel_image_list, name='carousel_image_list'),
    path('blog_admin/carousel_images/<int:pk>/edit/', views.carousel_image_edit, name='carousel_image_edit'),
    path('blog_admin/carousel_images/<int:pk>/delete/', views.carousel_image_delete, name='carousel_image_delete'),
]