from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'server.api'
    verbose_name = 'Fleet API'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import server.api.signals
            import server.api.signals_location
        except Exception as e:
            print(f"[OK] Warning: Could not import signals: {e}")
