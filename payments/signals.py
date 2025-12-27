from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PaymentRequest, PaymentCallback, PaymentReversal
from giving.models import GivingTransaction
import logging

logger = logging.getLogger('altar_funds')


@receiver(post_save, sender=PaymentRequest)
def payment_request_created(sender, instance, created, **kwargs):
    """Handle payment request creation"""
    if created:
        logger.info(f"Payment request created: {instance.request_id} for {instance.giving_transaction.transaction_id}")
        
        # Update giving transaction status
        if instance.giving_transaction.status == 'pending':
            instance.giving_transaction.status = 'processing'
            instance.giving_transaction.save()


@receiver(post_save, sender=PaymentCallback)
def payment_callback_processed(sender, instance, created, **kwargs):
    """Handle payment callback processing"""
    if created:
        logger.info(f"Payment callback received: {instance.callback_id} from {instance.provider}")
        
        # Update payment request if callback is linked
        if instance.payment_request:
            instance.payment_request.callback_received = True
            instance.payment_request.save()


@receiver(post_save, sender=PaymentReversal)
def payment_reversal_created(sender, instance, created, **kwargs):
    """Handle payment reversal creation"""
    if created:
        logger.info(f"Payment reversal created: {instance.reversal_id} for {instance.original_transaction.transaction_id}")
        
        # Update original transaction status if needed
        original_transaction = instance.original_transaction
        if original_transaction.status == 'completed' and instance.status == 'pending':
            original_transaction.status = 'reversal_pending'
            original_transaction.save()
