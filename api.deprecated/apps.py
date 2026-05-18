from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'Fleet API (DEPRECATED - Use server.api instead)'
    
    def ready(self):
        """Legacy app - do not use. All functionality moved to server.api"""
        pass
