import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from .services import AuditService

logger = logging.getLogger('altar_funds')


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests for audit purposes
    """
    
    def process_request(self, request):
        """Store request start time and details"""
        request._audit_start_time = time.time()
        request._audit_data = {
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': self.get_client_ip(request),
            'user': getattr(request.user, 'id', None) if not isinstance(request.user, AnonymousUser) else None,
        }
    
    def process_response(self, request, response):
        """Log request completion"""
        if hasattr(request, '_audit_data'):
            try:
                duration = time.time() - request._audit_start_time
                audit_data = request._audit_data
                audit_data.update({
                    'status_code': response.status_code,
                    'duration': duration,
                })
                
                # Log to audit service (async)
                AuditService.log_api_request.delay(audit_data)
                
            except Exception as e:
                logger.error(f"Audit middleware error: {e}")
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


import time
