"""
WSGI config for Logistics project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys

# Debug: Print startup information
print(f"[WSGI] Starting Django WSGI application", file=sys.stderr)
print(f"[WSGI] Python version: {sys.version}", file=sys.stderr)
print(f"[WSGI] Database URL set: {'DATABASE_URL' in os.environ}", file=sys.stderr)
print(f"[WSGI] DEBUG mode: {os.environ.get('DEBUG', 'NOT SET')}", file=sys.stderr)

from django.core.wsgi import get_wsgi_application

print(f"[WSGI] Importing Django core WSGI...", file=sys.stderr)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')

print(f"[WSGI] Setting Django settings module to: Logistics.settings", file=sys.stderr)

try:
    application = get_wsgi_application()
    print(f"[WSGI] ✓ Django WSGI application initialized successfully", file=sys.stderr)
except Exception as e:
    print(f"[WSGI] ✗ FAILED to initialize Django WSGI application", file=sys.stderr)
    print(f"[WSGI] Error: {type(e).__name__}: {e}", file=sys.stderr)
    import traceback
    print(f"[WSGI] Traceback:", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    raise
