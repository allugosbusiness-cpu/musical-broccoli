#!/usr/bin/env python
"""
Check database schema for fleet_missions table
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
from api.models import FleetMission

print("=== Database Schema Check ===")

# Check columns in fleet_missions table
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default 
        FROM information_schema.columns 
        WHERE table_name = 'fleet_missions' 
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    
    print("Current fleet_missions table columns:")
    for col in columns:
        print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
    
    # Check if max_speed column exists
    column_names = [col[0] for col in columns]
    if 'max_speed' in column_names:
        print("\n✓ max_speed column exists")
    else:
        print("\n✗ max_speed column missing")
        print("This is causing the error when creating missions via web app")

# Try to create a test mission
print("\n=== Testing Mission Creation ===")
try:
    # Check if we can create a mission
    mission = FleetMission.objects.create(
        mission_number="TEST_001",
        status="planned",
        origin={"lat": -1.2921, "lon": 36.8219},
        destination={"lat": -1.2864, "lon": 36.8175},
        distance_total_m=5000
    )
    print(f"✓ Test mission created successfully: {mission.id}")
    
    # Try to access max_speed property
    max_speed = mission.max_speed
    print(f"✓ max_speed property accessible: {max_speed}")
    
except Exception as e:
    print(f"✗ Error creating mission: {e}")
    print("This confirms the database schema issue")

print("\n=== SQL Fix ===")
# Read the SQL fix file
try:
    with open('server/fix_missing_columns.sql', 'r') as f:
        sql_content = f.read()
        print("SQL fix file content:")
        print(sql_content)
except Exception as e:
    print(f"Error reading SQL file: {e}")