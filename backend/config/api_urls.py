from django.urls import path, include
from rest_framework.routers import DefaultRouter
from reports.api import WasteReportViewSet, SupportTicketViewSet
from accounts.api import UserViewSet
from accounts.api_views import api_login, api_register
from notifications.api import NotificationViewSet

router = DefaultRouter()
router.register(r'waste-reports', WasteReportViewSet, basename='waste-report')
router.register(r'support-tickets', SupportTicketViewSet, basename='support-ticket')
router.register(r'users', UserViewSet, basename='user')
router.register(r'notifications', NotificationViewSet, basename='notification')

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('', include(router.urls)),
    path('login/', api_login, name='api-login'),
    path('register/', api_register, name='api-register'),
    
    # JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
