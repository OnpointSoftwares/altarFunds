from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import redis
from datetime import datetime

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    try:
        # Check database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # Check Redis connection
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    # Overall status
    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy"
    
    response_data = {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": db_status,
            "redis": redis_status,
        }
    }
    
    status_code = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(response_data, status=status_code)

urlpatterns = [
    path('health/', health_check, name='health_check'),
]
