from django.urls import path
from .views import HealthCheckView

app_name = 'common'

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health_check'),
]
