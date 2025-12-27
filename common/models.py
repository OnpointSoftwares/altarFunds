from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract base model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Abstract base model with soft delete functionality"""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Override delete to implement soft delete"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def hard_delete(self, using=None, keep_parents=False):
        """Actually delete from database"""
        super().delete(using=using, keep_parents=keep_parents)


class FinancialModel(TimeStampedModel):
    """Abstract base model for financial records"""
    # Financial records should never be deleted
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='%(class)s_updated'
    )
    
    class Meta:
        abstract = True
