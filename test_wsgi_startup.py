#!/usr/bin/env python
"""
Test WSGI application startup like Railway does
"""
import os
import sys

# Simulate Railway environment
print("Testing WSGI startup sequence...")
print("=" * 80)

# 1. Test basic Python import
print("\n1. Testing Python import...")
try:
    import django
    print(f"✓ Django {django.VERSION} imported successfully")
except Exception as e:
    print(f"✗ Failed to import Django: {e}")
    sys.exit(1)

# 2. Test settings import
print("\n2. Testing Django settings import...")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
    from django.conf import settings
    print(f"✓ Settings imported successfully")
    print(f"  - DEBUG: {settings.DEBUG}")
    print(f"  - INSTALLED_APPS count: {len(settings.INSTALLED_APPS)}")
except Exception as e:
    print(f"✗ Failed to import settings: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. Test Django setup
print("\n3. Testing Django setup...")
try:
    import django
    django.setup()
    print(f"✓ Django setup completed successfully")
except Exception as e:
    print(f"✗ Failed to setup Django: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Test WSGI application
print("\n4. Testing WSGI application...")
try:
    from Logistics.wsgi import application
    print(f"✓ WSGI application loaded: {application}")
except Exception as e:
    print(f"✗ Failed to load WSGI application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. Test simple request
print("\n5. Testing simple WSGI request...")
try:
    from io import BytesIO
    
    # Simulate a WSGI environ
    environ = {
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': BytesIO(),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }
    
    response_status = None
    response_headers = None
    
    def start_response(status, headers):
        global response_status, response_headers
        response_status = status
        response_headers = headers
        return lambda x: None
    
    response = application(environ, start_response)
    response_list = list(response)
    
    print(f"✓ WSGI application responded")
    print(f"  - Status: {response_status}")
    print(f"  - Response size: {sum(len(chunk) for chunk in response_list)} bytes")
    
    if response_status and '500' in response_status:
        print(f"\n✗ Application returned 500 error!")
        print("Response preview:")
        for chunk in response_list[:3]:
            print(chunk.decode('utf-8', errors='ignore')[:500])
    
except Exception as e:
    print(f"✗ Failed to test WSGI request: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("WSGI startup test completed successfully!")
print("If this works locally but fails on Railway, the issue is likely:")
print("  1. Missing environment variables (DATABASE_URL)")
print("  2. Database not reachable from Railway")
print("  3. Package version mismatch")
