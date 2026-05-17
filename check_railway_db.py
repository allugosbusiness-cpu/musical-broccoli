#!/usr/bin/env python
"""
Connect directly to Railway PostgreSQL database and check tables
"""

import os
import sys

# Try to get DATABASE_URL
db_url = os.environ.get('DATABASE_URL')

if not db_url:
    print("DATABASE_URL not set in environment")
    print("\nTrying to connect to a local/default Railway database...")
    # Common Railway PostgreSQL default
    db_url = "postgresql://postgres:postgres@localhost:5432/postgres"

print(f"Attempting to connect to: {db_url[:40]}...")

try:
    import psycopg2
    from urllib.parse import urlparse
    
    parsed = urlparse(db_url)
    
    conn = psycopg2.connect(
        host=parsed.hostname or 'localhost',
        port=parsed.port or 5432,
        database=parsed.path.lstrip('/') or 'postgres',
        user=parsed.username or 'postgres',
        password=parsed.password or 'postgres'
    )
    
    with conn.cursor() as cursor:
        # List all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"\nTables found: {len(tables)}")
        for (table,) in tables:
            print(f"  {table}")
        
        if not tables:
            print("\n  (No tables found - database is empty)")
    
    conn.close()
    
except ImportError:
    print("ERROR: psycopg2 not installed")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
