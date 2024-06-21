from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video_feed', views.video_feed, name='video_feed'),
    path('start_camera', views.start_camera, name='start_camera'),
    path('stop_camera', views.stop_camera, name='stop_camera'),
    path('upload_student', views.upload_student, name='upload_student'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('success/', views.success, name='success'),
    path('users/', views.admin_users, name='users'),
   
]
