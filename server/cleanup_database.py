#!/usr/bin/env python
"""
Standalone script to clean up old migration records from database.
Run this BEFORE django migrations to avoid orphaned migration errors.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from django.db import connection, ProgrammingError

def cleanup():
    """Delete orphaned migration records from database"""
    try:
        with connection.cursor() as cursor:
            # Check if django_migrations table exists
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'django_migrations'
                    )
                """)
                table_exists = cursor.fetchone()[0]
            elif connection.vendor == 'sqlite':
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name = 'django_migrations'
                """)
                table_exists = cursor.fetchone() is not None
            else:
                print("Unknown database vendor, skipping cleanup")
                return
            
            if not table_exists:
                print("✓ django_migrations table does not exist yet (first run)")
            else:
                # Delete all old api app migration records
                cursor.execute("DELETE FROM django_migrations WHERE app IN ('api', 'api.deprecated') OR app LIKE 'api.%'")
                deleted = cursor.rowcount
                
                if deleted > 0:
                    print(f"✓ Deleted {deleted} orphaned migration record(s)")
                else:
                    print("✓ No orphaned migration records found")
            
            # Drop old fleet tables that might exist from previous deployments
            tables_to_drop = [
                'fleet_admin_audit_logs',
                'fleet_driver_performance_daily',
                'fleet_dispute_comments',
                'fleet_disputes',
                'alerts',
                'fleet_activities',
                'fleet_truck_locations',
                'fleet_missions',
                'fleet_trucks',
                'fleet_drivers',
            ]
            
            for table in tables_to_drop:
                try:
                    if connection.vendor == 'postgresql':
                        cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
                    else:  # SQLite
                        cursor.execute(f'DROP TABLE IF EXISTS {table}')
                    print(f"✓ Dropped table: {table}")
                except Exception as drop_error:
                    # Table might not exist, which is fine
                    pass
                
    except Exception as e:
        print(f"✗ Error during cleanup: {e}")
        # Don't fail - just warn
        return

if __name__ == '__main__':
    print("Cleaning up old migration records...")
    cleanup()
    print("Done")
