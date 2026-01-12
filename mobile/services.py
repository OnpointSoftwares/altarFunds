import logging
import uuid
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import (
    MobileDevice, MobileAppVersion, UserSession, 
    MobileNotification, MobileAppAnalytics, MobileAppFeedback
)
from accounts.models import User
from common.services import NotificationService, AuditService

logger = logging.getLogger('altar_funds')


class MobileAuthService:
    """Mobile authentication service"""
    
    @staticmethod
    @transaction.atomic
    def register_device(device_data):
        """Register mobile device"""
        user = device_data.pop('user')
        device_token = device_data.get('device_token')

        if not device_token:
            device_token = f"anon-{uuid.uuid4()}"
            device_data['device_token'] = device_token
        
        # Check if device already exists
        device = MobileDevice.objects.filter(
            device_token=device_token,
            user=user
        ).first()
        
        if device:
            # Update existing device
            for key, value in device_data.items():
                if value is not None:
                    setattr(device, key, value)
            device.status = 'active'
            device.last_seen = timezone.now()
            device.save()
        else:
            # Create new device
            device = MobileDevice.objects.create(
                user=user,
                **device_data
            )
        
        logger.info(f"Mobile device registered: {device_token} for {user.email}")
        return device
    
    @staticmethod
    @transaction.atomic
    def create_session(user, device, request):
        """Create user session"""
        session_token = str(uuid.uuid4())
        expires_at = timezone.now() + timedelta(days=30)  # 30 days session
        
        session = UserSession.objects.create(
            user=user,
            device=device,
            session_token=session_token,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            expires_at=expires_at
        )
        
        # Clean up old sessions
        UserSession.objects.filter(
            user=user,
            expires_at__lt=timezone.now()
        ).delete()
        
        logger.info(f"Mobile session created: {session_token} for {user.email}")
        return session
    
    @staticmethod
    def validate_session(session_token):
        """Validate user session"""
        try:
            session = UserSession.objects.get(
                session_token=session_token,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            
            # Update last activity
            session.last_activity = timezone.now()
            session.save()
            
            return session
            
        except UserSession.DoesNotExist:
            return None
    
    @staticmethod
    def revoke_session(session_token):
        """Revoke user session"""
        try:
            session = UserSession.objects.get(session_token=session_token)
            session.is_active = False
            session.save()
            
            logger.info(f"Mobile session revoked: {session_token}")
            return True
            
        except UserSession.DoesNotExist:
            return False
    
    @staticmethod
    def compare_versions(version1, version2):
        """Compare two version strings"""
        def version_tuple(v):
            return tuple(map(int, (v.split("."))))
        
        v1 = version_tuple(version1)
        v2 = version_tuple(version2)
        
        return (v1 > v2) - (v1 < v2)
    
    @staticmethod
    def check_app_update(platform, current_version):
        """Check if app update is available"""
        latest_version = MobileAppVersion.objects.filter(
            platform=platform,
            status='production'
        ).first()
        
        if not latest_version:
            return {
                'update_available': False,
                'is_mandatory': False,
                'latest_version': None
            }
        
        update_available = MobileAuthService.compare_versions(
            current_version, latest_version.version
        ) < 0
        
        return {
            'update_available': update_available,
            'is_mandatory': latest_version.is_mandatory and update_available,
            'latest_version': latest_version.version,
            'download_url': latest_version.download_url,
            'update_message': latest_version.update_message,
            'release_notes': latest_version.release_notes
        }


class MobileNotificationService:
    """Mobile push notification service"""
    
    @staticmethod
    @transaction.atomic
    def send_push_notification(users=None, user_groups=None, churches=None,
                            title='', message='', data=None, notification_type='system'):
        """Send push notification to mobile devices"""
        from accounts.models import Member
        
        # Get target users
        target_users = set()
        
        if users:
            target_users.update(User.objects.filter(id__in=users))
        
        if user_groups:
            target_users.update(User.objects.filter(role__in=user_groups))
        
        if churches:
            target_users.update(
                User.objects.filter(church__id__in=churches)
            )
        
        if not target_users:
            return {'error': 'No target users specified'}
        
        # Get active devices for target users
        devices = MobileDevice.objects.filter(
            user__in=target_users,
            status='active'
        )
        
        notifications_created = 0
        notifications_sent = 0
        
        for device in devices:
            # Create notification record
            notification = MobileNotification.objects.create(
                user=device.user,
                device=device,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data or {}
            )
            notifications_created += 1
            
            # Send push notification
            try:
                result = MobileNotificationService._send_push_to_device(
                    device, title, message, data, notification_type
                )
                
                if result.get('success'):
                    notification.status = 'sent'
                    notification.sent_at = timezone.now()
                    notification.response_data = result
                    notifications_sent += 1
                else:
                    notification.status = 'failed'
                    notification.error_message = result.get('error', 'Unknown error')
                
                notification.save()
                
            except Exception as e:
                notification.status = 'failed'
                notification.error_message = str(e)
                notification.save()
                logger.error(f"Push notification failed: {e}")
        
        return {
            'notifications_created': notifications_created,
            'notifications_sent': notifications_sent,
            'devices_targeted': devices.count()
        }
    
    @staticmethod
    def _send_push_to_device(device, title, message, data, notification_type):
        """Send push notification to specific device"""
        # This would integrate with push notification services
        # For now, we'll simulate the push notification
        
        if device.device_type == 'android':
            return MobileNotificationService._send_android_push(
                device.device_token, title, message, data
            )
        elif device.device_type == 'ios':
            return MobileNotificationService._send_ios_push(
                device.device_token, title, message, data
            )
        else:
            return {'success': False, 'error': 'Unsupported device type'}
    
    @staticmethod
    def _send_android_push(device_token, title, message, data):
        """Send Android push notification using FCM"""
        try:
            # Placeholder for push notification implementation
            logger.info(f"Would send Android push to {device_token}: {title}")
            return {'success': True, 'message_id': 'placeholder'}
            
        except Exception as e:
            logger.error(f"Android push failed: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _send_ios_push(device_token, title, message, data):
        """Send iOS push notification using APNs"""
        try:
            # Placeholder for push notification implementation
            logger.info(f"Would send iOS push to {device_token}: {title}")
            return {'success': True, 'message_id': 'placeholder'}
            
        except Exception as e:
            logger.error(f"iOS push failed: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def mark_notification_delivered(notification_id):
        """Mark notification as delivered"""
        try:
            notification = MobileNotification.objects.get(id=notification_id)
            notification.status = 'delivered'
            notification.delivered_at = timezone.now()
            notification.save()
            
            return True
            
        except MobileNotification.DoesNotExist:
            return False
    
    @staticmethod
    def mark_notification_opened(notification_id):
        """Mark notification as opened"""
        try:
            notification = MobileNotification.objects.get(id=notification_id)
            notification.status = 'opened'
            notification.opened_at = timezone.now()
            notification.save()
            
            # Track analytics
            MobileAnalyticsService.track_event(
                user=notification.user,
                device=notification.device,
                event_type='notification',
                event_name='notification_opened',
                event_data={
                    'notification_id': notification_id,
                    'notification_type': notification.notification_type
                }
            )
            
            return True
            
        except MobileNotification.DoesNotExist:
            return False


class MobileAnalyticsService:
    """Mobile analytics service"""
    
    @staticmethod
    @transaction.atomic
    def track_event(user, device, event_type, event_name, event_data=None,
                    screen_name=None, session_id=None):
        """Track mobile app event"""
        analytics = MobileAppAnalytics.objects.create(
            user=user,
            device=device,
            event_type=event_type,
            event_name=event_name,
            event_data=event_data or {},
            screen_name=screen_name,
            session_id=session_id,
            event_timestamp=timezone.now()
        )
        
        logger.info(f"Analytics event tracked: {event_type} - {event_name} for {user.email}")
        return analytics
    
    @staticmethod
    def get_user_analytics(user, start_date=None, end_date=None):
        """Get user analytics data"""
        queryset = MobileAppAnalytics.objects.filter(user=user)
        
        if start_date:
            queryset = queryset.filter(event_timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(event_timestamp__lte=end_date)
        
        # Aggregate analytics
        analytics_data = {
            'total_events': queryset.count(),
            'unique_events': queryset.values('event_name').distinct().count(),
            'event_types': list(
                queryset.values('event_type').annotate(
                    count=models.Count('id')
                ).order_by('-count')
            ),
            'top_screens': list(
                queryset.filter(screen_name__isnull=False).values('screen_name').annotate(
                    count=models.Count('id')
                ).order_by('-count')[:10]
            ),
            'daily_usage': MobileAnalyticsService._get_daily_usage(queryset),
            'session_duration': MobileAnalyticsService._get_avg_session_duration(user)
        }
        
        return analytics_data
    
    @staticmethod
    def _get_daily_usage(queryset):
        """Get daily usage statistics"""
        from django.db.models import Count
        
        daily_data = queryset.extra(
            {'date': "date(event_timestamp)"}
        ).values('date').annotate(
            events=Count('id')
        ).order_by('date')
        
        return list(daily_data)
    
    @staticmethod
    def _get_avg_session_duration(user):
        """Get average session duration"""
        # This would calculate session duration based on session start/end events
        # For now, return placeholder
        return 0
    
    @staticmethod
    def get_app_analytics(start_date=None, end_date=None):
        """Get overall app analytics"""
        queryset = MobileAppAnalytics.objects.all()
        
        if start_date:
            queryset = queryset.filter(event_timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(event_timestamp__lte=end_date)
        
        # Aggregate app analytics
        app_analytics = {
            'total_users': queryset.values('user').distinct().count(),
            'total_devices': queryset.values('device').distinct().count(),
            'total_events': queryset.count(),
            'top_events': list(
                queryset.values('event_name').annotate(
                    count=models.Count('id')
                ).order_by('-count')[:20]
            ),
            'device_breakdown': list(
                queryset.values('device__device_type').annotate(
                    count=models.Count('id')
                ).order_by('-count')
            ),
            'daily_active_users': MobileAnalyticsService._get_daily_active_users(queryset),
            'retention_rate': MobileAnalyticsService._calculate_retention_rate()
        }
        
        return app_analytics
    
    @staticmethod
    def _get_daily_active_users(queryset):
        """Get daily active users"""
        from django.db.models import Count
        
        daily_data = queryset.extra(
            {'date': "date(event_timestamp)"}
        ).values('date').annotate(
            users=Count('user', distinct=True)
        ).order_by('date')
        
        return list(daily_data)
    
    @staticmethod
    def _calculate_retention_rate():
        """Calculate user retention rate"""
        # This would calculate retention based on user activity over time
        # For now, return placeholder
        return 0.0


class MobileFeedbackService:
    """Mobile feedback service"""
    
    @staticmethod
    @transaction.atomic
    def submit_feedback(user, feedback_data):
        """Submit mobile app feedback"""
        feedback = MobileAppFeedback.objects.create(
            user=user,
            **feedback_data
        )
        
        # Log feedback submission
        AuditService.log_user_action(
            user=user,
            action='MOBILE_FEEDBACK_SUBMITTED',
            details={
                'feedback_type': feedback.feedback_type,
                'title': feedback.title
            }
        )
        
        logger.info(f"Mobile feedback submitted: {feedback.title} by {user.email}")
        return feedback
    
    @staticmethod
    def get_feedback_list(status=None, feedback_type=None):
        """Get feedback list"""
        queryset = MobileAppFeedback.objects.all()
        
        if status:
            queryset = queryset.filter(status=status)
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def respond_to_feedback(feedback_id, admin_user, response):
        """Respond to feedback"""
        try:
            feedback = MobileAppFeedback.objects.get(id=feedback_id)
            feedback.admin_response = response
            feedback.responded_by = admin_user
            feedback.responded_at = timezone.now()
            feedback.status = 'resolved'
            feedback.save()
            
            # Send notification to user
            MobileNotificationService.send_push_notification(
                users=[feedback.user.id],
                title='Feedback Response',
                message=f'Your feedback "{feedback.title}" has been reviewed.',
                notification_type='system'
            )
            
            logger.info(f"Feedback responded: {feedback_id} by {admin_user.email}")
            return True
            
        except MobileAppFeedback.DoesNotExist:
            return False
