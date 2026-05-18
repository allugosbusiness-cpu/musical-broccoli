from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'server.api'
    verbose_name = 'Fleet API'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import api.signals
        except Exception as e:
            print(f"[OK] Warning: Could not import signals: {e}")
