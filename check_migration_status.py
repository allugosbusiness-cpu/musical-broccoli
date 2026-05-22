#!/usr/bin/env python
"""
Check Django migration status and apply missing migrations
"""
import os
import sys
import django

# Add server directory to path
sys.path.append('c:\\Users\\Mugogo\\Desktop\\musical-broccoli-main\\server')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.apps import apps

print("=== Checking Django Migration Status ===")

try:
    # Check current migration status
    print("Current migration status:")
    call_command('showmigrations', 'api', verbosity=1)
    
    print("\n=== Checking Applied Migrations ===")
    with connection.cursor() as cursor:
        cursor.execute("SELECT name, applied FROM django_migrations WHERE app = 'api' ORDER BY id;")
        migrations = cursor.fetchall()
        print("Applied migrations:")
        for name, applied in migrations:
            status = "✓" if applied else "✗"
            print(f"  {status} {name}")
    
    print("\n=== Checking Database Schema ===")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'fleet_missions' 
            AND column_name IN ('max_speed', 'avg_speed', 'compressed_trail')
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        if columns:
            print("✓ Missing columns already exist:")
            for col in columns:
                print(f"  {col[0]}: {col[1]}")
        else:
            print("✗ Missing columns still don't exist")
            print("Need to apply migrations")
    
    print("\n=== Attempting to Apply Migrations ===")
    try:
        call_command('migrate', 'api', verbosity=1)
        print("Migration applied successfully")
    except Exception as e:
        print(f"Migration error: {e}")
        print("This might be due to platform restrictions")
        
except Exception as e:
    print(f"Error checking migrations: {e}")

print("\n=== Alternative Approach ===")
print("If migrations cannot be applied automatically, we can try:")
print("1. Creating a new migration with different syntax")
print("2. Using the custom manager approach more extensively")
print("3. Modifying the model to be more flexible")