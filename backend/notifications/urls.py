from django.urls import path
from .api import NotificationViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

from . import views

urlpatterns = [
    path('center/', views.notification_center, name='notification_center'),
    path('mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
] + router.urls
