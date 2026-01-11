from django.urls import path
from .api import NotificationViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    # We can still keep simple paths if needed, but the router is better
    # However, since the user wants REST, let's use the router
] + router.urls
