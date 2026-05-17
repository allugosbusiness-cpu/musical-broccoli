"""
WSGI config for Logistics project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

# Ensure project root is in Python path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Debug: Print startup information
print(f"[WSGI] Starting Django WSGI application", file=sys.stderr)
print(f"[WSGI] Python version: {sys.version}", file=sys.stderr)
print(f"[WSGI] Working directory: {os.getcwd()}", file=sys.stderr)
print(f"[WSGI] Project root: {project_root}", file=sys.stderr)
print(f"[WSGI] Python path (first 3): {sys.path[:3]}", file=sys.stderr)
print(f"[WSGI] Database URL set: {'DATABASE_URL' in os.environ}", file=sys.stderr)
print(f"[WSGI] DEBUG mode: {os.environ.get('DEBUG', 'NOT SET')}", file=sys.stderr)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')

print(f"[WSGI] Setting Django settings module to: Logistics.settings", file=sys.stderr)

try:
    # Import Django WSGI first
    print(f"[WSGI] Attempting to import Django WSGI...", file=sys.stderr)
    from django.core.wsgi import get_wsgi_application
    print(f"[WSGI] ✓ Successfully imported Django WSGI", file=sys.stderr)
    
    # Now get the application
    print(f"[WSGI] Attempting to initialize WSGI application...", file=sys.stderr)
    application = get_wsgi_application()
    print(f"[WSGI] ✓ Django WSGI application initialized successfully", file=sys.stderr)
except ImportError as e:
    print(f"[WSGI] ✗ IMPORT ERROR: {type(e).__name__}: {e}", file=sys.stderr)
    print(f"[WSGI] This usually means a required package is not installed", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    raise
except Exception as e:
    print(f"[WSGI] ✗ FAILED to initialize Django WSGI application", file=sys.stderr)
    print(f"[WSGI] Error: {type(e).__name__}: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    raise
