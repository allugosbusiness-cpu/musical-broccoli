#!/usr/bin/env python
"""
Ensure database tables exist for v2 fleet schema
This handles cases where migrations are marked as applied but tables don't exist
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from django.db import connection
from django.apps import apps
from django.core.management import call_command

print("Starting database setup...")

# Force migrate all apps to ensure tables exist
try:
    print("Running migrations...")
    call_command('migrate', '--run-syncdb', verbosity=2)
    print("Migrations completed")
except Exception as e:
    print(f"Migration error: {e}")

# Verify v2 tables exist
from api.models_v2 import FleetDriver, FleetTruck, FleetMission

try:
    with connection.cursor() as cursor:
        # Check if fleet_trucks table exists
        if connection.vendor == 'postgresql':
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'fleet_trucks'
                )
            """)
        elif connection.vendor == 'sqlite':
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='fleet_trucks'
            """)
        
        result = cursor.fetchone()
        if connection.vendor == 'postgresql':
            table_exists = result[0]
        else:
            table_exists = bool(result)
        
        if table_exists:
            print("fleet_trucks table exists")
        else:
            print("WARNING: fleet_trucks table does not exist")

    # Try to query the models to verify they work
    truck_count = FleetTruck.objects.count()
    driver_count = FleetDriver.objects.count()
    mission_count = FleetMission.objects.count()
    
    print(f"Database check: {truck_count} trucks, {driver_count} drivers, {mission_count} missions")
    
except Exception as e:
    print(f"Error checking tables: {e}")
    import traceback
    traceback.print_exc()

print("Database setup complete")
