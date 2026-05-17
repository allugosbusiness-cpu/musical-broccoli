#!/usr/bin/env python
"""
Direct PostgreSQL table creation for production deployment
Falls back to Django if PostgreSQL not available
"""

import os
import sys

def create_via_postgresql():
    """Try to create FleetActivity table directly via PostgreSQL"""
    try:
        import psycopg2
        from psycopg2 import sql
    except ImportError:
        return False
    
    # Get DATABASE_URL from environment (Railway provides this)
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        return False
    
    print(f"Creating FleetActivity table via direct PostgreSQL connection...")
    
    try:
        # Connect directly to PostgreSQL
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Create FleetActivity table
        create_table_sql = """
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
            FOREIGN KEY (truck_id) REFERENCES fleet_trucks(id),
            FOREIGN KEY (driver_id) REFERENCES fleet_drivers(id),
            FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
        );
        
        -- Create indexes
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
        
        # Execute the SQL
        cursor.execute(create_table_sql)
        conn.commit()
        
        print("[OK] FleetActivity table and indexes created successfully in PostgreSQL")
        
        # Verify table exists
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'fleet_activities'
        """)
        
        if cursor.fetchone():
            print("[OK] Verified: fleet_activities table exists in database")
        else:
            print("WARNING: Table creation returned success but table not found")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"PostgreSQL creation failed: {e}")
        return False

def create_via_django():
    """Fall back to Django-based table creation"""
    print("Creating FleetActivity table via Django migrations...")
    
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
    django.setup()
    
    from django.core.management import execute_from_command_line
    
    # Run migrations to create table
    execute_from_command_line(['manage.py', 'migrate', 'api'])
    print("[OK] Django migrations completed")

if __name__ == '__main__':
    # Try PostgreSQL direct connection first
    if not create_via_postgresql():
        # Fall back to Django
        create_via_django()
    
    print("[OK] FleetActivity setup complete")
