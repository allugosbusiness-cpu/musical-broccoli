#!/usr/bin/env python
"""
Standalone script to clean up old migration records and tables from database.
Run this BEFORE django migrations to avoid orphaned migration errors.
Uses raw database connections to ensure commits are executed.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from django.db import connection
from django.conf import settings

def cleanup():
    """Delete orphaned migration records and drop old tables from database"""
    
    print("\n" + "=" * 70)
    print("DATABASE CLEANUP - Removing old api app traces")
    print("=" * 70)
    
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
    
    try:
        with connection.cursor() as cursor:
            # ===== STEP 1: DROP OLD TABLES (with autocommit) =====
            print("\nStep 1: Dropping old fleet tables...")
            print(f"Database vendor: {connection.vendor}")
            
            for table in tables_to_drop:
                try:
                    sql = f'DROP TABLE IF EXISTS "{table}" CASCADE' if connection.vendor == 'postgresql' else f'DROP TABLE IF EXISTS {table}'
                    print(f"  Executing: {sql}")
                    cursor.execute(sql)
                    print(f"    ✓ Success")
                except Exception as e:
                    print(f"    ✗ Error: {e}")
                    # Don't fail on individual table drops, but log it
            
            # Force connection to commit all changes
            connection.commit()
            print("  ✓ All DROP statements committed")
            
            # ===== STEP 2: DELETE MIGRATION RECORDS (with autocommit) =====
            print("\nStep 2: Cleaning migration records...")
            try:
                # Check if django_migrations table exists
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'django_migrations'
                    )
                """ if connection.vendor == 'postgresql' else """
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' AND name='django_migrations'
                """)
                exists = cursor.fetchone()[0] > 0 if connection.vendor == 'sqlite' else cursor.fetchone()[0]
                
                if exists:
                    # Delete old api migration records
                    sql = """
                        DELETE FROM django_migrations 
                        WHERE app IN ('api', 'api.deprecated') OR app LIKE 'api.%%'
                    """
                    print(f"  Executing: {sql[:50]}...")
                    cursor.execute(sql)
                    deleted = cursor.rowcount
                    connection.commit()
                    print(f"  ✓ Deleted {deleted} orphaned migration record(s) and committed")
                else:
                    print("  ✓ django_migrations table doesn't exist yet (first run)")
                    
            except Exception as e:
                print(f"  ⚠ Could not clean migration records: {e}")
                # Don't fail here - table might not exist yet
        
        print("\n" + "=" * 70)
        print("✓ CLEANUP SUCCESSFUL - Ready for migrations")
        print("=" * 70 + "\n")
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"✗ CLEANUP FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False

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
            print("\n✗ Cleanup failed - deployment will stop")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        print("\nDeployment stopped due to cleanup failure.")
        sys.exit(1)
