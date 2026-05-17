#!/usr/bin/env python
"""
Diagnostic script to test Railway environment and database connectivity
Run this on Railway to check if database is accessible
"""
import os
import sys
import django
import psycopg2
from urllib.parse import urlparse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

print("=" * 80)
print("RAILWAY ENVIRONMENT DIAGNOSTICS")
print("=" * 80)

# 1. Check environment variables
print("\n1. ENVIRONMENT VARIABLES")
print("-" * 80)
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Don't print the full URL with password
    parsed = urlparse(database_url)
    safe_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}/{parsed.path}"
    print(f"DATABASE_URL exists: {safe_url}")
    print(f"Full DATABASE_URL length: {len(database_url)} chars")
else:
    print("DATABASE_URL: NOT SET")

print(f"\nOther key env vars:")
print(f"  DJANGO_DEBUG: {os.environ.get('DJANGO_DEBUG', 'NOT SET')}")
print(f"  DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
print(f"  PYTHONPATH: {os.environ.get('PYTHONPATH', 'NOT SET')}")

# 2. Check Django database configuration
print("\n2. DJANGO DATABASE CONFIGURATION")
print("-" * 80)
from django.conf import settings
for db_name, db_config in settings.DATABASES.items():
    print(f"Database '{db_name}':")
    print(f"  ENGINE: {db_config.get('ENGINE', 'NOT SET')}")
    print(f"  NAME: {db_config.get('NAME', 'NOT SET')}")
    print(f"  HOST: {db_config.get('HOST', 'NOT SET')}")
    print(f"  PORT: {db_config.get('PORT', 'NOT SET')}")
    print(f"  USER: {db_config.get('USER', 'NOT SET')}")

# 3. Test Django database connection
print("\n3. DJANGO DATABASE CONNECTION TEST")
print("-" * 80)
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result:
            print("✓ Django database connection: SUCCESS")
            print(f"  Query result: {result}")
        else:
            print("✗ Django database connection: Failed to execute query")
except Exception as e:
    print(f"✗ Django database connection: FAILED")
    print(f"  Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

# 4. Check if migrations are applied
print("\n4. MIGRATIONS STATUS")
print("-" * 80)
try:
    from django.core.management import call_command
    from io import StringIO
    
    out = StringIO()
    call_command('showmigrations', 'api', stdout=out)
    migration_output = out.getvalue()
    
    # Check for applied migrations
    applied_count = migration_output.count('[X]')
    unapplied_count = migration_output.count('[ ]')
    
    print(f"Applied migrations: {applied_count}")
    print(f"Unapplied migrations: {unapplied_count}")
    
    if unapplied_count > 0:
        print("\n⚠ WARNING: Some migrations are not applied!")
        print("Recent migration status:")
        for line in migration_output.split('\n')[-10:]:
            if line.strip():
                print(f"  {line}")
except Exception as e:
    print(f"✗ Could not check migration status")
    print(f"  Error: {type(e).__name__}: {str(e)}")

# 5. Test models can be imported
print("\n5. MODEL IMPORTS")
print("-" * 80)
try:
    from api.models_v2 import FleetTruck, FleetDriver, FleetMission
    print("✓ FleetTruck: OK")
    print("✓ FleetDriver: OK")
    print("✓ FleetMission: OK")
except Exception as e:
    print(f"✗ Model import failed: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

# 6. Check if tables exist
print("\n6. DATABASE TABLES")
print("-" * 80)
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        if tables:
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("✗ No tables found in public schema!")
except Exception as e:
    print(f"✗ Could not query tables: {type(e).__name__}: {str(e)}")

# 7. Django system check
print("\n7. DJANGO SYSTEM CHECK")
print("-" * 80)
try:
    from django.core.management import call_command
    from io import StringIO
    
    out = StringIO()
    err = StringIO()
    call_command('check', stdout=out, stderr=err)
    
    check_output = out.getvalue()
    if 'identified no issues' in check_output:
        print("✓ System check: PASSED")
    else:
        print("⚠ System check output:")
        print(check_output)
        if err.getvalue():
            print("Errors:")
            print(err.getvalue())
except Exception as e:
    print(f"✗ System check failed: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 80)
print("DIAGNOSTICS COMPLETE")
print("=" * 80)
