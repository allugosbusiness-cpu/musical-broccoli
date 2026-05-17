#!/usr/bin/env python
"""
Create v2 schema tables using Django ORM if they don't exist
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from api.models_v2 import (
    FleetDriver, FleetTruck, FleetMission, FleetMissionStop,
    FleetMissionEvent, FleetMissionDispute, FleetDriverPerformanceDaily,
    FleetAdminAuditLog, FleetTruckLocation
)

print("Creating v2 schema tables...")

# Get the executor
executor = MigrationExecutor(connection)

# Try to get leaf node migrations (the latest)
try:
    leaf_nodes = executor.loader.graph.leaf_nodes()
    print(f"Found {len(leaf_nodes)} leaf migration nodes")
except Exception as e:
    print(f"Error getting leaf nodes: {e}")

# Try to run all pending migrations
try:
    executor.migrate(executor.loader.graph.leaf_nodes())
    print("Migrations executed")
except Exception as e:
    print(f"Migration execution failed: {e}")

# Now use Django's schema editor to create tables for models that don't have them
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import StateApps
from django.db import DEFAULT_DB_ALIAS
from django.db.backends.base.schema import BaseSchemEditor

print("\nCreating model tables via schema editor...")

models_to_create = [
    FleetDriver, FleetTruck, FleetMission, FleetMissionStop,
    FleetMissionEvent, FleetMissionDispute, FleetDriverPerformanceDaily,
    FleetAdminAuditLog, FleetTruckLocation
]

with connection.schema_editor() as schema_editor:
    for model in models_to_create:
        table_name = model._meta.db_table
        try:
            with connection.cursor() as cursor:
                # Check if table exists
                if connection.vendor == 'postgresql':
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = '{table_name}'
                        )
                    """)
                    exists = cursor.fetchone()[0]
                else:  # sqlite
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    exists = bool(cursor.fetchone())
            
            if not exists:
                print(f"Creating table: {table_name}")
                schema_editor.create_model(model)
            else:
                print(f"Table exists: {table_name}")
        except Exception as e:
            print(f"Error with {table_name}: {e}")

print("\nSchema creation complete")
