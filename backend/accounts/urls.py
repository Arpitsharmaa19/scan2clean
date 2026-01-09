from django.urls import path
from .views import (
    login_view,
    register_view,
    logout_view,
    redirect_dashboard,
    citizen_dashboard,
    worker_dashboard,
    admin_dashboard,
    become_worker
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),

    path('dashboard/', redirect_dashboard, name='dashboard'),
    path('dashboard/citizen/', citizen_dashboard, name='citizen_dashboard'),
    path('dashboard/worker/', worker_dashboard, name='worker_dashboard'),
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),
    path('become-worker/', become_worker, name='become_worker'),
    
]
