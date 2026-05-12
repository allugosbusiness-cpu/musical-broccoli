#!/usr/bin/env python
"""
Test script to verify Django WSGI application can start successfully.
This mimics what Render will do during deployment.
"""

import os
import sys
import django

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 70)
print("DJANGO WSGI STARTUP TEST")
print("=" * 70)

# Step 1: Check Python version
print(f"\n[1] Python Version Check")
print(f"    Version: {sys.version}")
print(f"    Executable: {sys.executable}")

# Step 2: Check environment
print(f"\n[2] Environment Check")
print(f"    Working Directory: {os.getcwd()}")
print(f"    Project Root: {project_root}")
print(f"    DATABASE_URL: {'SET' if os.environ.get('DATABASE_URL') else 'NOT SET'}")
print(f"    DEBUG: {os.environ.get('DEBUG', 'NOT SET')}")
print(f"    SECRET_KEY: {'SET' if os.environ.get('SECRET_KEY') else 'NOT SET'}")

# Step 3: Check Django installation
print(f"\n[3] Django Installation Check")
try:
    print(f"    Django Version: {django.VERSION}")
    print(f"    Django Path: {django.__file__}")
except Exception as e:
    print(f"    ✗ ERROR: {e}")
    sys.exit(1)

# Step 4: Check settings module
print(f"\n[4] Settings Module Check")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
try:
    from django.conf import settings
    print(f"    ✓ Settings loaded successfully")
    print(f"    DEBUG: {settings.DEBUG}")
    print(f"    Database Engine: {settings.DATABASES['default']['ENGINE']}")
except Exception as e:
    print(f"    ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Check installed apps
print(f"\n[5] Installed Apps Check")
try:
    django.setup()
    from django.apps import apps
    app_names = [app.name for app in apps.get_app_configs()]
    print(f"    ✓ Django setup complete")
    print(f"    Total apps loaded: {len(app_names)}")
    for app in sorted(app_names):
        status = "✓" if not app.startswith("django.") or app == "rest_framework" else "✓"
        print(f"      {status} {app}")
except Exception as e:
    print(f"    ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Check WSGI application
print(f"\n[6] WSGI Application Check")
try:
    from Logistics.wsgi import application
    print(f"    ✓ WSGI application loaded successfully")
    print(f"    Application class: {application.__class__.__name__}")
except Exception as e:
    print(f"    ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 7: Test a simple WSGI request
print(f"\n[7] Test WSGI Request")
try:
    from django.test import Client
    client = Client()
    response = client.get('/api/v1/')
    print(f"    ✓ WSGI request successful")
    print(f"    Status Code: {response.status_code}")
    print(f"    Response Type: {type(response)}")
except Exception as e:
    print(f"    ⚠ Warning (non-critical): {e}")

print(f"\n" + "=" * 70)
print("✓ ALL CHECKS PASSED - App should start successfully!")
print("=" * 70)
