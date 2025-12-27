from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger('altar_funds')

User = get_user_model()

@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    """Log when a new user is created"""
    if created:
        logger.info(f"New user created: {instance.email} (ID: {instance.id})")
        
        # Send welcome notification
        from common.services import send_email_notification
        if instance.email:
            subject = "Welcome to AltarFunds"
            message = f"""
            Dear {instance.full_name},
            
            Welcome to AltarFunds - your unified church finance platform!
            
            Your account has been created with the role: {instance.get_role_display()}
            
            Please log in to get started.
            
            God bless you!
            
            AltarFunds Team
            """
            send_email_notification.delay(subject, message, [instance.email])
