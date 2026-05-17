#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

# Check existing tables
with connection.cursor() as cursor:
    # Get all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    
    print(f"Total tables: {len(tables)}")
    print("\nFleet-related tables:")
    for (table,) in tables:
        if 'fleet' in table.lower():
            print(f"  ✓ {table}")
    
    # Check migration status
    print("\n\nMigration history:")
    recorder = MigrationRecorder(connection)
    for app, migration in recorder.applied_migrations():
        if app == 'api':
            print(f"  [X] {app} - {migration}")

print("\nChecking if we need to recreate tables...")

# Try to access the models
from api.models_v2 import FleetTruck, FleetDriver, FleetMission

try:
    count = FleetTruck.objects.count()
    print(f"FleetTruck count: {count}")
except Exception as e:
    print(f"Error accessing FleetTruck: {e}")
