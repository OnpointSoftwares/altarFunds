from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger('altar_funds')


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the error response format
        custom_response_data = {
            'error': True,
            'status_code': response.status_code,
            'message': get_error_message(exc),
            'details': response.data,
            'timestamp': context['request'].META.get('HTTP_X_REQUEST_TIME', None)
        }
        
        # Log the error
        logger.error(
            f"API Error: {exc} - Status: {response.status_code} - "
            f"User: {context['request'].user} - Path: {context['request'].path}"
        )
        
        response.data = custom_response_data
    
    return response


def get_error_message(exc):
    """Extract user-friendly error message from exception"""
    if isinstance(exc, ValidationError):
        if hasattr(exc, 'message_dict'):
            return 'Validation error: ' + str(exc.message_dict)
        return 'Validation error: ' + str(exc)
    elif isinstance(exc, PermissionError):
        return 'You do not have permission to perform this action'
    elif hasattr(exc, 'detail'):
        return str(exc.detail)
    return str(exc)


class AltarFundsException(Exception):
    """Base exception for AltarFunds application"""
    
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class InsufficientFundsException(AltarFundsException):
    """Raised when insufficient funds for a transaction"""
    
    def __init__(self, message="Insufficient funds for this transaction"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class DuplicateTransactionException(AltarFundsException):
    """Raised when attempting to process a duplicate transaction"""
    
    def __init__(self, message="This transaction appears to be a duplicate"):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


class InvalidMpesaCallbackException(AltarFundsException):
    """Raised when M-Pesa callback validation fails"""
    
    def __init__(self, message="Invalid M-Pesa callback signature"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class ChurchRegistrationException(AltarFundsException):
    """Raised when church registration fails"""
    
    def __init__(self, message="Church registration failed"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class UnauthorizedAccessException(AltarFundsException):
    """Raised when user lacks required permissions"""
    
    def __init__(self, message="You are not authorized to perform this action"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)
