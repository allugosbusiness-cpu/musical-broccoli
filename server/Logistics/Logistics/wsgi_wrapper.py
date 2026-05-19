"""
WSGI wrapper that ensures all tables exist before handling requests
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from django.core.wsgi import get_wsgi_application
from django.db import connection

# Ensure FleetActivity table exists
print("[WSGI] Ensuring FleetActivity table exists...")

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM fleet_activities LIMIT 1")
    print("[WSGI] Table already exists")
except Exception as e:
    print(f"[WSGI] Table missing, attempting to create: {e}")
    try:
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
        
        with connection.cursor() as cursor:
            cursor.execute(sql)
        connection.commit()
        print("[WSGI] FleetActivity table created successfully")
    except Exception as create_error:
        print(f"[WSGI] WARNING: Could not create FleetActivity table: {create_error}")

print("[WSGI] Initialization complete\n")

# Get the actual WSGI application
application = get_wsgi_application()
