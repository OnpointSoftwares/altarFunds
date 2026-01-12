import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from common.services import NotificationService
from common.exceptions import AltarFundsException

logger = logging.getLogger('altar_funds')
User = get_user_model()


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def verify_phone_number(user, verification_code):
        """Verify phone number with OTP code"""
        # For now, we'll mark as verified
        user.is_phone_verified = True
        user.save(update_fields=['is_phone_verified'])
        return True
    
    @staticmethod
    def send_phone_verification(user):
        """Send phone verification code"""
        # This would integrate with SMS service
        notification = f"Your verification code for AltarFunds is 123456"
        
        if user.phone_number:
            logger.info(f"Would send SMS to {user.phone_number}: {notification}")
        
        return True


class UserService:
    """Service for user management operations"""
    
    @staticmethod
    @transaction.atomic
    def create_user_with_member_profile(user_data, member_data=None):
        """Create user with member profile"""
        try:
            # Create user
            user = User.objects.create_user(**user_data)
            
            # Create member profile
            if member_data is None:
                member_data = {}
            
            member_data['user'] = user
            from .models import Member
            member = Member.objects.create(**member_data)
            
            # Generate membership number if church is set
            if user.church:
                member.generate_membership_number()
            
            # Send welcome notification
            NotificationService.send_welcome_notification(user)
            
            logger.info(f"Created user: {user.email} with member profile")
            return user, member
            
        except Exception as e:
            logger.error(f"Failed to create user with member profile: {e}")
            raise AltarFundsException("User creation failed")
    
    @staticmethod
    def update_user_role(user, new_role, updated_by):
        """Update user role with audit trail"""
        if user.role == new_role:
            return user
        
        old_role = user.role
        user.role = new_role
        user.save(update_fields=['role'])
        
        # Log role change
        from common.services import AuditService
        AuditService.log_user_action(
            user=updated_by,
            action='ROLE_CHANGE',
            details={
                'target_user': user.email,
                'old_role': old_role,
                'new_role': new_role
            }
        )
        
        # Notify user of role change
        NotificationService.send_role_change_notification(user, old_role, new_role)
        
        logger.info(f"Updated role for {user.email}: {old_role} -> {new_role}")
        return user
    
    @staticmethod
    def transfer_user_to_church(user, new_church, transferred_by):
        """Transfer user to different church"""
        if user.church == new_church:
            return user
        
        old_church = user.church
        user.church = new_church
        user.save(update_fields=['church'])
        
        # Update member profile
        try:
            member = user.member_profile
            member.generate_membership_number()  # Generate new membership number
        except User.member_profile.RelatedObjectDoesNotExist:
            pass
        
        # Log transfer
        from common.services import AuditService
        AuditService.log_user_action(
            user=transferred_by,
            action='CHURCH_TRANSFER',
            details={
                'target_user': user.email,
                'old_church': old_church.name if old_church else None,
                'new_church': new_church.name
            }
        )
        
        logger.info(f"Transferred {user.email} to {new_church.name}")
        return user
    
    @staticmethod
    def deactivate_user(user, deactivated_by, reason=None):
        """Deactivate user account"""
        if not user.is_active:
            return user
        
        user.is_active = False
        user.save(update_fields=['is_active'])
        
        # Log deactivation
        from common.services import AuditService
        AuditService.log_user_action(
            user=deactivated_by,
            action='USER_DEACTIVATION',
            details={
                'target_user': user.email,
                'reason': reason or 'No reason provided'
            }
        )
        
        # Notify user
        NotificationService.send_account_deactivation_notification(user, reason)
        
        logger.info(f"Deactivated user: {user.email}")
        return user
    
    @staticmethod
    def reactivate_user(user, reactivated_by):
        """Reactivate user account"""
        if user.is_active:
            return user
        
        user.is_active = True
        user.is_suspended = False
        user.suspension_reason = ''
        user.suspended_until = None
        user.save(update_fields=['is_active', 'is_suspended', 'suspension_reason', 'suspended_until'])
        
        # Log reactivation
        from common.services import AuditService
        AuditService.log_user_action(
            user=reactivated_by,
            action='USER_REACTIVATION',
            details={'target_user': user.email}
        )
        
        # Notify user
        NotificationService.send_account_reactivation_notification(user)
        
        logger.info(f"Reactivated user: {user.email}")
        return user


class SessionService:
    """Service for user session management"""
    
    @staticmethod
    def cleanup_expired_sessions():
        """Clean up expired sessions"""
        from .models import UserSession
        
        expired_sessions = UserSession.objects.filter(
            expires_at__lt=timezone.now()
        )
        
        count = expired_sessions.count()
        expired_sessions.update(is_active=False)
        
        logger.info(f"Cleaned up {count} expired sessions")
        return count
    
    @staticmethod
    def revoke_all_user_sessions(user):
        """Revoke all active sessions for a user"""
        from .models import UserSession
        
        sessions = UserSession.objects.filter(
            user=user,
            is_active=True
        )
        
        count = sessions.count()
        sessions.update(is_active=False)
        
        logger.info(f"Revoked {count} sessions for user: {user.email}")
        return count
    
    @staticmethod
    def get_active_session_count(user):
        """Get number of active sessions for user"""
        from .models import UserSession
        
        return UserSession.objects.filter(
            user=user,
            is_active=True
        ).count()


class MemberService:
    """Service for member management operations"""
    
    @staticmethod
    def update_membership_status(member, new_status, updated_by):
        """Update member's membership status"""
        if member.membership_status == new_status:
            return member
        
        old_status = member.membership_status
        member.membership_status = new_status
        member.save(update_fields=['membership_status'])
        
        # Log status change
        from common.services import AuditService
        AuditService.log_user_action(
            user=updated_by,
            action='MEMBERSHIP_STATUS_CHANGE',
            details={
                'member': member.user.email,
                'old_status': old_status,
                'new_status': new_status
            }
        )
        
        logger.info(f"Updated membership status for {member.user.email}: {old_status} -> {new_status}")
        return member
    
    @staticmethod
    def add_member_to_department(member, department, added_by):
        """Add member to department"""
        if department in member.departments.all():
            return member
        
        member.departments.add(department)
        
        # Log department addition
        from common.services import AuditService
        AuditService.log_user_action(
            user=added_by,
            action='DEPARTMENT_ASSIGNMENT',
            details={
                'member': member.user.email,
                'department': department.name
            }
        )
        
        logger.info(f"Added {member.user.email} to {department.name}")
        return member
    
    @staticmethod
    def remove_member_from_department(member, department, removed_by):
        """Remove member from department"""
        if department not in member.departments.all():
            return member
        
        member.departments.remove(department)
        
        # Log department removal
        from common.services import AuditService
        AuditService.log_user_action(
            user=removed_by,
            action='DEPARTMENT_REMOVAL',
            details={
                'member': member.user.email,
                'department': department.name
            }
        )
        
        logger.info(f"Removed {member.user.email} from {department.name}")
        return member
    
    @staticmethod
    def calculate_member_giving_summary(member, start_date=None, end_date=None):
        """Calculate member's giving summary"""
        from giving.models import GivingTransaction
        
        queryset = GivingTransaction.objects.filter(member=member)
        
        if start_date:
            queryset = queryset.filter(transaction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_date__lte=end_date)
        
        summary = queryset.aggregate(
            total_amount=models.Sum('amount'),
            total_count=models.Count('id'),
            avg_amount=models.Avg('amount')
        )
        
        return {
            'total_amount': summary['total_amount'] or 0,
            'total_transactions': summary['total_count'] or 0,
            'average_amount': summary['avg_amount'] or 0,
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }
