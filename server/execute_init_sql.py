#!/usr/bin/env python
"""
Direct SQL execution script for creating tables
"""

import os
import sys


def execute_sql_file():
    """Execute SQL file directly on PostgreSQL"""
    
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("[SQL] No DATABASE_URL, skipping")
        return False
    
    print("[SQL] Executing init_fleet_activity.sql on PostgreSQL...")
    
    try:
        import psycopg2
    except ImportError:
        print("[SQL] psycopg2 not available")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Read SQL file
        with open('init_fleet_activity.sql', 'r') as f:
            sql = f.read()
        
        # Execute SQL
        cursor.execute(sql)
        conn.commit()
        
        print("[SQL] OK - SQL executed successfully")
        
        # Verify table exists
        cursor.execute("SELECT COUNT(*) FROM fleet_activities")
        count = cursor.fetchone()[0]
        print(f"[SQL] OK - Verified: {count} records in fleet_activities")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[SQL] ERROR: {e}")
        return False


if __name__ == '__main__':
    if not execute_sql_file():
        sys.exit(1)
    print("[SQL] Complete\n")
