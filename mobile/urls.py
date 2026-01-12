from django.urls import path
from . import views

app_name = 'mobile'

urlpatterns = [
    # Authentication
    path('login/', views.MobileLoginView.as_view(), name='login'),
    path('google-login/', views.MobileGoogleLoginView.as_view(), name='google-login'),
    path('register/', views.MobileRegisterView.as_view(), name='register'),
    path('register-device/', views.MobileRegisterDeviceView.as_view(), name='register-device'),
    path('devices/', views.MobileDeviceListView.as_view(), name='device-list'),
    path('devices/<int:pk>/', views.MobileDeviceDetailView.as_view(), name='device-detail'),
    
    # App Configuration
    path('config/', views.MobileAppConfigView.as_view(), name='app-config'),
    
    # User Profile & Data
    path('profile/', views.MobileUserProfileView.as_view(), name='user-profile'),
    path('giving-summary/', views.MobileGivingSummaryView.as_view(), name='giving-summary'),
    path('church-info/', views.MobileChurchInfoView.as_view(), name='church-info'),
    path('quick-actions/', views.MobileQuickActionsView.as_view(), name='quick-actions'),
    
    # Notifications
    path('notifications/', views.MobileNotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', views.MobileNotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/send/', views.mobile_send_push_notification, name='send-push-notification'),
    
    # Analytics
    path('analytics/track/', views.mobile_track_analytics, name='track-analytics'),
    
    # Feedback
    path('feedback/submit/', views.mobile_submit_feedback, name='submit-feedback'),
]
