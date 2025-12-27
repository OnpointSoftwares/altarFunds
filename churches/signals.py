from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Church, Campus, Department, SmallGroup
from .services import ChurchService
import logging

logger = logging.getLogger('altar_funds')


@receiver(pre_save, sender=Church)
def church_pre_save(sender, instance, **kwargs):
    """Handle church pre-save operations"""
    # Normalize email
    if instance.email:
        instance.email = instance.email.lower()
    
    # Generate church code if not set
    if not instance.church_code and instance.city:
        # Use city abbreviation + sequence
        city_abbr = instance.city[:3].upper() if instance.city else 'UNK'
        
        # Get last sequence for this city
        from .models import Church
        last_church = Church.objects.filter(
            church_code__startswith=city_abbr
        ).order_by('-church_code').first()
        
        if last_church and last_church.church_code:
            sequence = int(last_church.church_code[3:]) + 1
        else:
            sequence = 1
        
        instance.church_code = f"{city_abbr}{sequence:03d}"


@receiver(post_save, sender=Church)
def church_created(sender, instance, created, **kwargs):
    """Handle church creation"""
    if created:
        logger.info(f"New church created: {instance.name} ({instance.church_code})")
        
        # Create default departments if church is verified
        if instance.is_verified:
            create_default_departments(instance)


@receiver(post_save, sender=Campus)
def campus_created(sender, instance, created, **kwargs):
    """Handle campus creation"""
    if created:
        logger.info(f"New campus created: {instance.name} for {instance.church.name}")


@receiver(post_save, sender=Department)
def department_created(sender, instance, created, **kwargs):
    """Handle department creation"""
    if created:
        logger.info(f"New department created: {instance.name} for {instance.church.name}")


@receiver(post_save, sender=SmallGroup)
def small_group_created(sender, instance, created, **kwargs):
    """Handle small group creation"""
    if created:
        logger.info(f"New small group created: {instance.name} for {instance.church.name}")


def create_default_departments(church):
    """Create default departments for a new church"""
    default_departments = [
        {
            'name': 'Worship Ministry',
            'department_type': 'worship',
            'description': 'Responsible for worship services and music ministry'
        },
        {
            'name': 'Children Ministry',
            'department_type': 'children',
            'description': 'Responsible for children\'s programs and Sunday school'
        },
        {
            'name': 'Youth Ministry',
            'department_type': 'youth',
            'description': 'Responsible for youth programs and activities'
        },
        {
            'name': 'Men Ministry',
            'department_type': 'men',
            'description': 'Responsible for men\'s fellowship and programs'
        },
        {
            'name': 'Women Ministry',
            'department_type': 'women',
            'description': 'Responsible for women\'s fellowship and programs'
        },
        {
            'name': 'Outreach Ministry',
            'department_type': 'outreach',
            'description': 'Responsible for community outreach and evangelism'
        },
        {
            'name': 'Administration',
            'department_type': 'admin',
            'description': 'Responsible for church administration and operations'
        }
    ]
    
    for dept_data in default_departments:
        Department.objects.get_or_create(
            church=church,
            name=dept_data['name'],
            defaults={
                'department_type': dept_data['department_type'],
                'description': dept_data['description'],
                'is_active': True
            }
        )
    
    logger.info(f"Created default departments for {church.name}")
