#!/usr/bin/env python
"""
Test database configuration and connection
"""

import os
import sys

print("=== Database Configuration Test ===")
print(f"DATABASE_URL env var: {'SET' if 'DATABASE_URL' in os.environ else 'NOT SET'}")

# Show Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')

import django
from django.conf import settings

print(f"\nDjango Database Configuration:")
print(f"Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"Name: {settings.DATABASES['default'].get('NAME', 'N/A')}")
print(f"Host: {settings.DATABASES['default'].get('HOST', 'N/A')}")
print(f"Port: {settings.DATABASES['default'].get('PORT', 'N/A')}")

# Try connecting
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("\n✓ Database connection successful")
        
        # Check what tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"\nTables in database: {len(tables)}")
        if tables:
            for (table,) in tables[:10]:
                if 'fleet' in table.lower() or 'kpi' in table.lower():
                    print(f"  {table}")
        
except Exception as e:
    print(f"\n✗ Database connection failed: {e}")
    print(f"Error type: {type(e).__name__}")
    sys.exit(1)
