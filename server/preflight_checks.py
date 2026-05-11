#!/usr/bin/env python
"""
Pre-flight checks before starting the web server
Ensures all required tables exist
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from django.db import connection


def ensure_fleet_activity_exists():
    """Ensure FleetActivity table exists before web server starts"""
    
    print("[PRE-FLIGHT] Checking FleetActivity table...")
    
    with connection.cursor() as cursor:
        try:
            cursor.execute("SELECT COUNT(*) FROM fleet_activities LIMIT 1")
            count = cursor.fetchone()[0]
            print(f"[PRE-FLIGHT] OK - FleetActivity table exists with {count} records")
            return True
        except Exception as e:
            print(f"[PRE-FLIGHT] ERROR - FleetActivity table missing: {e}")
            return False

def create_fleet_activity_directly():
    """Create FleetActivity table directly using raw SQL"""
    
    print("[PRE-FLIGHT] Creating FleetActivity table directly...")
    
    sql = """
    CREATE TABLE IF NOT EXISTS fleet_activities (
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
    );
    
    CREATE INDEX IF NOT EXISTS idx_fleet_activities_fleet_type_ts 
        ON fleet_activities(fleet_id, activity_type, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_fleet_activities_truck_date 
        ON fleet_activities(truck_id, activity_date);
    CREATE INDEX IF NOT EXISTS idx_fleet_activities_driver_date 
        ON fleet_activities(driver_id, activity_date);
    CREATE INDEX IF NOT EXISTS idx_fleet_activities_mission_ts 
        ON fleet_activities(mission_id, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_fleet_activities_category_ts 
        ON fleet_activities(activity_category, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_fleet_activities_critical_ts 
        ON fleet_activities(is_critical, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_fleet_activities_ts 
        ON fleet_activities(timestamp DESC);
    """
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
        connection.commit()
        print("[PRE-FLIGHT] OK - FleetActivity table created")
        return True
    except Exception as e:
        print(f"[PRE-FLIGHT] WARNING - Could not create table: {e}")
        return False


if __name__ == '__main__':
    print("\n" + "="*60)
    print("FLEET MANAGEMENT PRE-FLIGHT CHECKS")
    print("="*60 + "\n")
    
    # Check if table exists
    if not ensure_fleet_activity_exists():
        # Try to create it
        if not create_fleet_activity_directly():
            print("[PRE-FLIGHT] CRITICAL - Could not ensure FleetActivity table")
            print("[PRE-FLIGHT] Web server may not function properly")
    
    print("[PRE-FLIGHT] Checks complete - ready to start web server\n")
