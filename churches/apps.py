from django.apps import AppConfig


class ChurchesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'churches'
    
    def ready(self):
        import churches.signals
