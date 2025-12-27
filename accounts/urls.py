from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile Management
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.PasswordChangeView.as_view(), name='change-password'),
    
    # Password Reset
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Sessions
    path('sessions/', views.UserSessionListView.as_view(), name='sessions'),
    path('sessions/<int:session_id>/revoke/', views.revoke_session, name='revoke-session'),
    
    # User Management (Admin)
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/suspend/', views.suspend_user, name='suspend-user'),
    path('users/<int:user_id>/unsuspend/', views.unsuspend_user, name='unsuspend-user'),
]
