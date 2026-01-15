"""URL Configuration for AltarFunds project"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Modules
    path('api/accounts/', include('accounts.urls')),
    path('api/mobile/', include('mobile.urls')),
    path('api/churches/', include('churches.urls')),
    path('api/giving/', include('giving.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/expenses/', include('expenses.urls')),
    path('api/budgets/', include('budgets.urls')),
    path('api/donations/', include('donations.urls')),
    path('api/members/', include('members.urls')),
    path('api/accounting/', include('accounting.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/audit/', include('audit.urls')),
    path('api/notifications/', include('notifications.urls')),
    
    # Health check
    path('api/health/', include('common.urls')),

    # Dashboard
    path('dashboard/', include('dashboard.urls')),

    # Template-based Authentication
    path('', include('accounts.auth_urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
