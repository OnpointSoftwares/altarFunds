import logging
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from twilio.rest import Client
import firebase_admin
from firebase_admin import messaging

logger = logging.getLogger('altar_funds')


@shared_task
def send_email_notification(subject, message, recipient_list, html_message=None):
    """Send email notification asynchronously"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email sent to {recipient_list}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")


@shared_task
def send_whatsapp_notification(to, message):
    """Send WhatsApp notification asynchronously"""
    try:
        # Initialize Twilio client (you'll need to configure these)
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        client = Client(account_sid, auth_token)
        
        # Send WhatsApp message
        message = client.messages.create(
            body=message,
            from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
            to=f'whatsapp:{to}'
        )
        
        logger.info(f"WhatsApp message sent to {to}")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")


@shared_task
def send_push_notification(title, body, data, registration_tokens):
    """Send push notification via Firebase Cloud Messaging"""
    try:
        # Initialize Firebase Admin SDK if not already initialized
        if not firebase_admin._apps:
            cred = firebase_admin.credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        
        # Create message
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data,
            tokens=registration_tokens,
        )
        
        # Send message
        response = messaging.send_multicast(message)
        logger.info(f"Push notification sent: {response.success_count} successful, {response.failure_count} failed")
        
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")


class NotificationService:
    """Service for sending notifications through various channels"""
    
    @staticmethod
    def send_giving_confirmation(member, amount, transaction_id):
        """Send giving confirmation to member"""
        subject = f"Thank you for your gift of KES {amount}"
        message = f"""
        Dear {member.full_name},
        
        Thank you for your generous gift of KES {amount}.
        Transaction ID: {transaction_id}
        
        God bless you!
        
        AltarFunds Team
        """
        
        # Send email
        if member.email:
            send_email_notification.delay(subject, message, [member.email])
        
        # Send SMS/WhatsApp
        if member.phone_number:
            whatsapp_message = f"Thank you for your gift of KES {amount}. Transaction ID: {transaction_id}"
            send_whatsapp_notification.delay(member.phone_number, whatsapp_message)
    
    @staticmethod
    def send_payment_failure_notification(member, amount, error_message):
        """Send payment failure notification"""
        subject = f"Payment Failed - KES {amount}"
        message = f"""
        Dear {member.full_name},
        
        Your payment of KES {amount} failed.
        Reason: {error_message}
        
        Please try again or contact support.
        
        AltarFunds Team
        """
        
        if member.email:
            send_email_notification.delay(subject, message, [member.email])
    
    @staticmethod
    def send_expense_approval_request(approvers, expense):
        """Send expense approval request to authorized approvers"""
        subject = f"Expense Approval Required - KES {expense.amount}"
        message = f"""
        An expense of KES {expense.amount} requires your approval.
        
        Description: {expense.description}
        Submitted by: {expense.created_by.full_name}
        Date: {expense.created_at.strftime('%Y-%m-%d %H:%M')}
        
        Please review and approve in the AltarFunds portal.
        """
        
        recipient_emails = [approver.email for approver in approvers if approver.email]
        if recipient_emails:
            send_email_notification.delay(subject, message, recipient_emails)


@shared_task
def log_api_request(audit_data):
    """Log API request for audit purposes"""
    try:
        from audit.models import AuditLog
        from django.contrib.auth.models import AnonymousUser
        
        user_id = audit_data.get('user')
        if user_id:
            from accounts.models import User
            user = User.objects.get(id=user_id)
        else:
            user = None
        
        AuditLog.objects.create(
            user=user,
            action='API_REQUEST',
            details=audit_data,
            ip_address=audit_data.get('ip_address'),
            user_agent=audit_data.get('user_agent'),
        )
        
    except Exception as e:
        logger.error(f"Failed to log API request: {e}")


class AuditService:
    """Service for audit logging"""
    
    @staticmethod
    def log_financial_transaction(user, action, amount, details):
        """Log financial transaction for audit"""
        from audit.models import AuditLog
        
        AuditLog.objects.create(
            user=user,
            action=action,
            amount=amount,
            details=details,
            ip_address='SYSTEM',  # For system-generated transactions
        )
    
    @staticmethod
    def log_user_action(user, action, details, ip_address=None):
        """Log user action for audit"""
        from audit.models import AuditLog
        
        AuditLog.objects.create(
            user=user,
            action=action,
            details=details,
            ip_address=ip_address or 'SYSTEM',
        )
