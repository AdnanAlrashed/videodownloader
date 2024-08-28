# video/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('get-info/', views.get_video_info, name='get_video_info'),
    path('download/', views.download_video, name='download_video'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
