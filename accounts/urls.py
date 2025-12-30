from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, 
    UserLoginView, 
    logout_view, 
    UserProfileView, 
    PasswordChangeView, 
    PasswordResetRequestView, 
    PasswordResetConfirmView, 
    UserSessionListView, 
    revoke_session, 
    UserListView, 
    UserDetailView
)

app_name = 'accounts'

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('sessions/', UserSessionListView.as_view(), name='sessions'),
    path('sessions/<int:session_id>/revoke/', revoke_session, name='revoke_session'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
]
