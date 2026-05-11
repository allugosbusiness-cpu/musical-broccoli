#!/usr/bin/env python
"""
Initialize database before web server starts
Ensures FleetActivity table exists
"""

import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from django.db import connection

print("\n" + "="*70)
print("DATABASE INITIALIZATION")
print("="*70 + "\n")

# Check and create FleetActivity table
sql_statements = [
    """CREATE TABLE IF NOT EXISTS fleet_activities (
        id UUID PRIMARY KEY,
        fleet_id UUID NOT NULL,
        truck_id UUID,
        driver_id UUID,
        mission_id UUID,
        activity_type VARCHAR(50) NOT NULL,
        activity_category VARCHAR(50),
        location_lat NUMERIC(10,6),
        location_lon NUMERIC(10,6),
        location_name VARCHAR(255),
        speed_kmh NUMERIC(5,2),
        distance_m NUMERIC(12,2),
        fuel_liters NUMERIC(10,2),
        fuel_percentage NUMERIC(5,2),
        alert_level VARCHAR(20),
        breach_type VARCHAR(50),
        violation_details TEXT,
        mission_status_before VARCHAR(50),
        mission_status_after VARCHAR(50),
        metadata JSONB DEFAULT '{}',
        activity_date DATE,
        activity_time TIME,
        timestamp TIMESTAMP,
        is_critical BOOLEAN DEFAULT FALSE,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (truck_id) REFERENCES fleet_trucks(id) ON DELETE SET NULL,
        FOREIGN KEY (driver_id) REFERENCES fleet_drivers(id) ON DELETE SET NULL,
        FOREIGN KEY (mission_id) REFERENCES fleet_missions(id) ON DELETE SET NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_fleet_activities_fleet_type_ts ON fleet_activities(fleet_id, activity_type, timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_fleet_activities_truck_date ON fleet_activities(truck_id, activity_date)",
    "CREATE INDEX IF NOT EXISTS idx_fleet_activities_driver_date ON fleet_activities(driver_id, activity_date)",
    "CREATE INDEX IF NOT EXISTS idx_fleet_activities_mission_ts ON fleet_activities(mission_id, timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_fleet_activities_category_ts ON fleet_activities(activity_category, timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_fleet_activities_critical_ts ON fleet_activities(is_critical, timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_fleet_activities_ts ON fleet_activities(timestamp DESC)",
]

try:
    with connection.cursor() as cursor:
        for sql in sql_statements:
            try:
                cursor.execute(sql)
            except Exception as e:
                if "already exists" in str(e).lower():
                    pass
                else:
                    raise
    
    connection.commit()
    print("[OK] FleetActivity table initialized successfully")
    
except Exception as e:
    print(f"[WARNING] FleetActivity initialization: {e}")

# Verify table exists
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM fleet_activities")
        count = cursor.fetchone()[0]
    print(f"[OK] Verified: fleet_activities exists with {count} records\n")
except Exception as e:
    print(f"[ERROR] Failed to verify table: {e}\n")
    sys.exit(1)
