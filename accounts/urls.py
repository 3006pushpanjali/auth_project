from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path(
    'verify-email/<uuid:token>/',
    views.verify_email,
    name='verify_email'
    ),
    path(
    'forgot-password/',
    views.forgot_password,
    name='forgot_password'
    ),
    path(
    'reset-password/<uuid:token>/',
    views.reset_password,
    name='reset_password'
    ),
]