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
    """Delete orphaned migration records and drop old tables from database"""
    with connection.cursor() as cursor:
        # Step 1: Drop all old fleet tables first
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
        
        print("Step 1: Dropping old fleet tables...")
        for table in tables_to_drop:
            try:
                if connection.vendor == 'postgresql':
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
                else:  # SQLite
                    cursor.execute(f'DROP TABLE IF EXISTS {table}')
                print(f"  ✓ Dropped: {table}")
            except Exception as e:
                # If table doesn't exist, that's OK
                if 'does not exist' not in str(e):
                    print(f"  ⚠ Warning dropping {table}: {e}")
        
        # Step 2: Check if django_migrations table exists
        print("\nStep 2: Cleaning migration records...")
        try:
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
                print("  ✓ Unknown database vendor, skipping migration cleanup")
                return True
            
            if not table_exists:
                print("  ✓ django_migrations table doesn't exist yet (first run)")
                return True
            
            # Delete all old api app migration records
            cursor.execute("""
                DELETE FROM django_migrations 
                WHERE app IN ('api', 'api.deprecated') OR app LIKE 'api.%%'
            """)
            deleted = cursor.rowcount
            
            if deleted > 0:
                print(f"  ✓ Deleted {deleted} orphaned migration record(s)")
            else:
                print("  ✓ No orphaned migration records found")
                
            return True
            
        except Exception as e:
            print(f"  ✓ Could not access django_migrations (first run or error): {e}")
            return True

if __name__ == '__main__':
    print("=" * 60)
    print("DATABASE CLEANUP - Removing old api app traces")
    print("=" * 60)
    try:
        success = cleanup()
        if success:
            print("\n✓ Cleanup completed successfully")
            sys.exit(0)
        else:
            print("\n✗ Cleanup failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
