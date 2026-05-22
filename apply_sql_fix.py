#!/usr/bin/env python
"""
Apply SQL fix to add missing max_speed, avg_speed, and compressed_trail columns
"""
import os
import sys
import django

# Add server directory to path
sys.path.append('c:\\Users\\Mugogo\\Desktop\\musical-broccoli-main\\server')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

print("=== Applying Database Schema Fix ===")

# Read the SQL fix file
sql_file = 'server/fix_missing_columns.sql'
try:
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    print(f"Reading SQL fix from: {sql_file}")
    
    # Extract the ALTER TABLE statements
    alter_statements = []
    lines = sql_content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('ALTER TABLE fleet_missions ADD COLUMN'):
            alter_statements.append(line)
    
    print(f"Found {len(alter_statements)} ALTER TABLE statements:")
    for stmt in alter_statements:
        print(f"  {stmt}")
    
    # Execute the ALTER TABLE statements
    with connection.cursor() as cursor:
        for stmt in alter_statements:
            try:
                print(f"Executing: {stmt}")
                cursor.execute(stmt)
                print("✓ Success")
            except Exception as e:
                print(f"✗ Error: {e}")
                if "column already exists" in str(e):
                    print("  Column already exists, skipping...")
                else:
                    raise
        
        # Verify the columns were added
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'fleet_missions' 
            AND column_name IN ('max_speed', 'avg_speed', 'compressed_trail')
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        print("\n=== Verification ===")
        if columns:
            print("✓ Missing columns have been added:")
            for col in columns:
                print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        else:
            print("✗ Columns not found, there may have been an issue")
    
    print("\n=== Testing Mission Creation ===")
    try:
        from api.models import FleetMission
        
        # Try to create a test mission
        mission = FleetMission.objects.create(
            mission_number="TEST_FIX_001",
            status="planned",
            origin={"lat": -1.2921, "lon": 36.8219},
            destination={"lat": -1.2864, "lon": 36.8175},
            distance_total_m=5000
        )
        print(f"✓ Test mission created successfully: {mission.id}")
        
        # Try to access max_speed property
        max_speed = mission.max_speed
        print(f"✓ max_speed property accessible: {max_speed}")
        
        # Clean up test mission
        mission.delete()
        print("✓ Test mission cleaned up")
        
    except Exception as e:
        print(f"✗ Error creating test mission: {e}")

except Exception as e:
    print(f"Error: {e}")
    print("The SQL fix file may not exist or there may be an issue with the database connection")