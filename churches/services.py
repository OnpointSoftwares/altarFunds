import logging
from django.db import transaction, models
from django.utils import timezone
from .models import Church, Campus, Department, SmallGroup, ChurchBankAccount, MpesaAccount
from common.services import AuditService, NotificationService
from common.exceptions import AltarFundsException

logger = logging.getLogger('altar_funds')


class ChurchService:
    """Service for church management operations"""
    
    @staticmethod
    @transaction.atomic
    def register_church(church_data, registered_by):
        """Register a new church"""
        try:
            church = Church.objects.create(
                status='pending',
                is_verified=False,
                **church_data
            )
            church.generate_church_code()
            
            # Log registration
            AuditService.log_user_action(
                user=registered_by,
                action='CHURCH_REGISTRATION',
                details={
                    'church': church.name,
                    'church_code': church.church_code,
                    'email': church.email,
                    'phone': church.phone_number
                }
            )
            
            # Send notifications to denomination admins
            NotificationService.send_church_registration_notification(church)
            
            logger.info(f"Church registered: {church.name} ({church.church_code})")
            return church
            
        except Exception as e:
            logger.error(f"Failed to register church: {e}")
            raise AltarFundsException("Church registration failed")
    
    @staticmethod
    @transaction.atomic
    def verify_church(church, verified_by):
        """Verify a church"""
        if church.is_verified:
            raise AltarFundsException("Church is already verified")
        
        church.verify(verified_by)
        
        # Log verification
        AuditService.log_user_action(
            user=verified_by,
            action='CHURCH_VERIFICATION',
            details={
                'church': church.name,
                'church_code': church.church_code
            }
        )
        
        # Send verification notification
        NotificationService.send_church_verification_notification(church)
        
        logger.info(f"Church verified: {church.name} by {verified_by.email}")
        return church
    
    @staticmethod
    @transaction.atomic
    def update_church_status(church, new_status, updated_by, reason=None):
        """Update church status"""
        old_status = church.status
        church.status = new_status
        
        if new_status == 'verified' and not church.is_verified:
            church.is_verified = True
            church.verification_date = timezone.now()
            church.verified_by = updated_by
        elif new_status == 'suspended':
            church.is_active = False
        elif new_status == 'closed':
            church.is_active = False
        
        church.save()
        
        # Log status change
        AuditService.log_user_action(
            user=updated_by,
            action='CHURCH_STATUS_CHANGE',
            details={
                'church': church.name,
                'old_status': old_status,
                'new_status': new_status,
                'reason': reason or 'Status updated'
            }
        )
        
        # Send notification if applicable
        if new_status == 'suspended':
            NotificationService.send_church_suspension_notification(church, reason)
        
        logger.info(f"Church status updated: {church.name} - {old_status} -> {new_status}")
        return church
    
    @staticmethod
    def get_church_statistics(church):
        """Get comprehensive church statistics"""
        from accounts.models import Member
        from giving.models import GivingTransaction
        from accounting.models import Expense
        
        # Member statistics
        total_members = Member.objects.filter(user__church=church).count()
        active_members = Member.objects.filter(
            user__church=church,
            user__is_active=True,
            membership_status='member'
        ).count()
        
        # Giving statistics (current month)
        now = timezone.now()
        monthly_giving = GivingTransaction.objects.filter(
            member__user__church=church,
            transaction_date__year=now.year,
            transaction_date__month=now.month,
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        # Expense statistics (current month)
        monthly_expenses = Expense.objects.filter(
            church=church,
            expense_date__year=now.year,
            expense_date__month=now.month,
            status='approved'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        # Campus, department, and small group counts
        campus_count = church.campuses.filter(is_active=True).count()
        department_count = church.departments.filter(is_active=True).count()
        small_group_count = church.small_groups.filter(is_active=True).count()
        
        return {
            'members': {
                'total': total_members,
                'active': active_members,
                'growth_rate': calculate_growth_rate(church)
            },
            'finances': {
                'monthly_giving': monthly_giving,
                'monthly_expenses': monthly_expenses,
                'net_income': monthly_giving - monthly_expenses,
                'year_to_date_giving': get_year_to_date_giving(church),
                'year_to_date_expenses': get_year_to_date_expenses(church)
            },
            'organization': {
                'campuses': campus_count,
                'departments': department_count,
                'small_groups': small_group_count
            }
        }


class CampusService:
    """Service for campus management operations"""
    
    @staticmethod
    @transaction.atomic
    def create_campus(campus_data, created_by):
        """Create a new campus"""
        campus = Campus.objects.create(**campus_data)
        
        # Log creation
        AuditService.log_user_action(
            user=created_by,
            action='CAMPUS_CREATION',
            details={
                'campus': campus.name,
                'church': campus.church.name,
                'city': campus.city
            }
        )
        
        logger.info(f"Campus created: {campus.name} for {campus.church.name}")
        return campus
        
    @staticmethod
    @transaction.atomic
    def set_main_campus(campus, set_by):
        """Set as main campus"""
        church = campus.church
        
        # Unset all other main campuses
        Campus.objects.filter(church=church, is_main_campus=True).update(is_main_campus=False)
        
        # Set this as main campus
        campus.is_main_campus = True
        campus.save()
        
        # Log change
        AuditService.log_user_action(
            user=set_by,
            action='MAIN_CAMPUS_CHANGE',
            details={
                'campus': campus.name,
                'church': church.name
            }
        )
        
        logger.info(f"Main campus set: {campus.name} for {church.name}")
        return campus


class DepartmentService:
    """Service for department management operations"""
    
    @staticmethod
    @transaction.atomic
    def create_department(department_data, created_by):
        """Create a department"""
        department = Department.objects.create(**department_data)
        
        # Log creation
        AuditService.log_user_action(
            user=created_by,
            action='DEPARTMENT_CREATION',
            details={
                'department': department.name,
                'church': department.church.name,
                'type': department.department_type
            }
        )
        
        logger.info(f"Department created: {department.name} for {department.church.name}")
        return department
    
    @staticmethod
    def get_department_budget_summary(department, year=None):
        """Get department budget summary"""
        from accounting.models import Budget, Expense
        
        if not year:
            year = timezone.now().year
        
        # Get budget
        budget = Budget.objects.filter(
            department=department,
            year=year,
            is_active=True
        ).first()
        
        # Get actual expenses
        expenses = Expense.objects.filter(
            department=department,
            expense_date__year=year,
            status='approved'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return {
            'budget_amount': budget.amount if budget else 0,
            'actual_expenses': expenses,
            'remaining': (budget.amount if budget else 0) - expenses,
            'utilization_percentage': (expenses / (budget.amount if budget else 1)) * 100
        }


class SmallGroupService:
    """Service for small group management operations"""
    
    @staticmethod
    @transaction.atomic
    def create_small_group(group_data, created_by):
        """Create a small group"""
        small_group = SmallGroup.objects.create(**group_data)
        
        # Log creation
        AuditService.log_user_action(
            user=created_by,
            action='SMALL_GROUP_CREATION',
            details={
                'group': small_group.name,
                'church': small_group.church.name,
                'type': small_group.group_type
            }
        )
        
        logger.info(f"Small group created: {small_group.name} for {small_group.church.name}")
        return small_group
    
    @staticmethod
    def add_member_to_group(small_group, member, added_by):
        """Add member to small group"""
        if small_group.is_full:
            raise AltarFundsException("Small group is at maximum capacity")
        
        member.small_group = small_group
        member.save()
        
        # Log addition
        AuditService.log_user_action(
            user=added_by,
            action='SMALL_GROUP_MEMBER_ADDITION',
            details={
                'member': member.user.email,
                'group': small_group.name,
                'church': small_group.church.name
            }
        )
        
        logger.info(f"Member added to group: {member.user.email} -> {small_group.name}")
        return member
    
    @staticmethod
    def remove_member_from_group(small_group, member, removed_by):
        """Remove member from small group"""
        member.small_group = None
        member.save()
        
        # Log removal
        AuditService.log_user_action(
            user=removed_by,
            action='SMALL_GROUP_MEMBER_REMOVAL',
            details={
                'member': member.user.email,
                'group': small_group.name,
                'church': small_group.church.name
            }
        )
        
        logger.info(f"Member removed from group: {member.user.email} <- {small_group.name}")
        return member


class BankAccountService:
    """Service for bank account management operations"""
    
    @staticmethod
    @transaction.atomic
    def create_bank_account(account_data, created_by):
        """Create a bank account"""
        account = ChurchBankAccount.objects.create(**account_data)
        
        # Set as primary if first account
        if account.church.bank_accounts.count() == 1:
            account.is_primary = True
            account.save()
        
        # Log creation
        AuditService.log_user_action(
            user=created_by,
            action='BANK_ACCOUNT_CREATION',
            details={
                'account': account.account_name,
                'church': account.church.name,
                'bank': account.bank_name,
                'account_number': account.account_number[-4:]  # Last 4 digits only
            }
        )
        
        logger.info(f"Bank account created: {account.account_name} for {account.church.name}")
        return account
    
    @staticmethod
    @transaction.atomic
    def set_primary_account(account, set_by):
        """Set as primary bank account"""
        church = account.church
        
        # Unset all other primary accounts
        ChurchBankAccount.objects.filter(church=church, is_primary=True).update(is_primary=False)
        
        # Set this as primary
        account.is_primary = True
        account.save()
        
        # Log change
        AuditService.log_user_action(
            user=set_by,
            action='PRIMARY_BANK_ACCOUNT_CHANGE',
            details={
                'account': account.account_name,
                'church': church.name,
                'bank': account.bank_name
            }
        )
        
        logger.info(f"Primary bank account set: {account.account_name} for {church.name}")
        return account


class MpesaAccountService:
    """Service for M-Pesa account management operations"""
    
    @staticmethod
    @transaction.atomic
    def create_mpesa_account(account_data, created_by):
        """Create an M-Pesa account"""
        account = MpesaAccount.objects.create(**account_data)
        
        # Log creation
        AuditService.log_user_action(
            user=created_by,
            action='MPESA_ACCOUNT_CREATION',
            details={
                'account': account.account_name,
                'church': account.church.name,
                'type': account.account_type,
                'business_number': account.business_number
            }
        )
        
        logger.info(f"M-Pesa account created: {account.account_name} for {account.church.name}")
        return account
    
    @staticmethod
    def validate_mpesa_credentials(account):
        """Validate M-Pesa API credentials"""
        try:
            # This would integrate with M-Pesa API to validate credentials
            # For now, we'll just check if required fields are present
            
            if not account.consumer_key or not account.consumer_secret:
                raise AltarFundsException("Consumer key and secret are required")
            
            if account.account_type == 'paybill' and not account.passkey:
                raise AltarFundsException("Passkey is required for Paybill accounts")
            
            return True
            
        except Exception as e:
            logger.error(f"M-Pesa credential validation failed: {e}")
            raise AltarFundsException("M-Pesa credential validation failed")
    
    @staticmethod
    def test_mpesa_connection(account):
        """Test M-Pesa API connection"""
        try:
            # This would make a test API call to M-Pesa
            # For now, we'll just validate the credentials
            MpesaAccountService.validate_mpesa_credentials(account)
            
            logger.info(f"M-Pesa connection test successful: {account.account_name}")
            return True
            
        except Exception as e:
            logger.error(f"M-Pesa connection test failed: {e}")
            raise AltarFundsException("M-Pesa connection test failed")


# Helper functions
def calculate_growth_rate(church):
    """Calculate church membership growth rate"""
    from accounts.models import Member
    from datetime import timedelta
    
    now = timezone.now()
    last_month = now - timedelta(days=30)
    three_months_ago = now - timedelta(days=90)
    
    current_members = Member.objects.filter(
        user__church=church,
        user__is_active=True
    ).count()
    
    last_month_members = Member.objects.filter(
        user__church=church,
        user__is_active=True,
        created_at__lte=last_month
    ).count()
    
    three_months_members = Member.objects.filter(
        user__church=church,
        user__is_active=True,
        created_at__lte=three_months_ago
    ).count()
    
    if three_months_members == 0:
        return 0
    
    growth_rate = ((current_members - three_months_members) / three_months_members) * 100
    return round(growth_rate, 2)


def get_year_to_date_giving(church):
    """Get year-to-date giving for church"""
    from giving.models import GivingTransaction
    
    now = timezone.now()
    return GivingTransaction.objects.filter(
        member__user__church=church,
        transaction_date__year=now.year,
        status='completed'
    ).aggregate(total=models.Sum('amount'))['total'] or 0


def get_year_to_date_expenses(church):
    """Get year-to-date expenses for church"""
    from accounting.models import Expense
    
    now = timezone.now()
    return Expense.objects.filter(
        church=church,
        expense_date__year=now.year,
        status='approved'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
