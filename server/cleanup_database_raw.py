#!/usr/bin/env python
"""
Standalone script using RAW database connections to clean up old tables.
Bypasses Django's transaction management to ensure commits happen.
"""
import os
import sys

def cleanup_postgresql(db_url):
    """Clean up database using raw psycopg2 connection"""
    import psycopg2
    
    print("  Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True  # Enable autocommit
        cursor = conn.cursor()
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return False
    
    try:
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
        
        print("  Dropping tables with CASCADE...")
        for table in tables_to_drop:
            try:
                sql = f'DROP TABLE IF EXISTS "{table}" CASCADE'
                cursor.execute(sql)
                print(f"    ✓ {table}")
            except Exception as e:
                print(f"    ⚠ {table}: {e}")
        
        print("  Cleaning django_migrations...")
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app IN ('api', 'api.deprecated') OR app LIKE 'api.%%'")
            deleted = cursor.rowcount
            print(f"    ✓ Deleted {deleted} migration record(s)")
        except Exception as e:
            print(f"    ⚠ {e}")
        
        cursor.close()
        conn.close()
        print("  ✓ Connection closed")
        return True
    except Exception as e:
        print(f"  ✗ Error during cleanup: {e}")
        try:
            cursor.close()
            conn.close()
        except:
            pass
        return False

def cleanup_sqlite(db_path):
    """Clean up database using raw sqlite3 connection"""
    import sqlite3
    
    print(f"  Connecting to SQLite at {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        conn.isolation_level = None  # Autocommit mode
        cursor = conn.cursor()
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return False
    
    try:
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
        
        print("  Dropping tables...")
        for table in tables_to_drop:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table}')
                print(f"    ✓ {table}")
            except Exception as e:
                print(f"    ⚠ {table}: {e}")
        
        print("  Cleaning django_migrations...")
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app IN ('api', 'api.deprecated') OR app LIKE 'api.%'")
            deleted = cursor.rowcount
            print(f"    ✓ Deleted {deleted} migration record(s)")
        except Exception as e:
            print(f"    ⚠ {e}")
        
        cursor.close()
        conn.close()
        print("  ✓ Connection closed")
        return True
    except Exception as e:
        print(f"  ✗ Error during cleanup: {e}")
        try:
            cursor.close()
            conn.close()
        except:
            pass
        return False

def main():
    print("\n" + "=" * 70)
    print("DATABASE CLEANUP - Raw Connection Approach")
    print("=" * 70)
    
    # Get database URL from environment
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("\n✗ DATABASE_URL not set!")
        return False
    
    print(f"\nDatabase URL: {db_url[:50]}...")
    
    try:
        if db_url.startswith('postgres://') or db_url.startswith('postgresql://'):
            print("Using PostgreSQL cleanup...")
            success = cleanup_postgresql(db_url)
        elif db_url.endswith('.sqlite3') or 'sqlite' in db_url:
            print("Using SQLite cleanup...")
            success = cleanup_sqlite(db_url)
        else:
            print(f"Unknown database URL format")
            return False
        
        if success:
            print("\n" + "=" * 70)
            print("✓ CLEANUP COMPLETE - Database ready for migrations")
            print("=" * 70 + "\n")
            return True
        else:
            print("\n✗ Cleanup had errors")
            return False
            
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
