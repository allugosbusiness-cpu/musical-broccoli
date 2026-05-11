#!/usr/bin/env python
"""
Emergency database setup - force create all v2 tables using raw SQL
This handles cases where migrations failed to create tables
"""

import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from django.db import connection

print("="*60)
print("EMERGENCY DATABASE SETUP")
print("="*60)

# Get database type
db_vendor = connection.vendor
print(f"\nDatabase type: {db_vendor}")
print(f"Database name: {connection.settings_dict.get('NAME', 'unknown')}")

# SQL to create v2 schema tables for PostgreSQL
postgresql_sql = """
-- Drop existing fleet tables if they exist (for fresh start)
DROP TABLE IF EXISTS fleet_truck_locations CASCADE;
DROP TABLE IF EXISTS fleet_mission_events CASCADE;
DROP TABLE IF EXISTS fleet_mission_disputes CASCADE;
DROP TABLE IF EXISTS fleet_mission_stops CASCADE;
DROP TABLE IF EXISTS fleet_missions CASCADE;
DROP TABLE IF EXISTS fleet_driver_performance_daily CASCADE;
DROP TABLE IF EXISTS fleet_trucks CASCADE;
DROP TABLE IF EXISTS fleet_drivers CASCADE;
DROP TABLE IF EXISTS fleet_admin_audit_logs CASCADE;

-- Create fleet_drivers table
CREATE TABLE fleet_drivers (
    id UUID PRIMARY KEY,
    fleet_id UUID NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(254) UNIQUE,
    license_number VARCHAR(50) UNIQUE,
    license_state VARCHAR(10),
    hire_date DATE,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    on_duty BOOLEAN DEFAULT FALSE,
    performance_mark NUMERIC(5,2) DEFAULT 0,
    deliveries_count INT DEFAULT 0,
    last_active_at TIMESTAMP,
    achievements JSONB DEFAULT '{}',
    photo_url VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create fleet_trucks table
CREATE TABLE fleet_trucks (
    id UUID PRIMARY KEY,
    fleet_id UUID NOT NULL,
    truck_identifier VARCHAR(50) NOT NULL,
    plate VARCHAR(50) NOT NULL UNIQUE,
    vin VARCHAR(50) UNIQUE,
    telematics_id VARCHAR(100),
    make VARCHAR(100),
    model VARCHAR(100),
    year INT,
    fuel_capacity_liters NUMERIC(10,2),
    fuel_consumed_liters NUMERIC(10,2) DEFAULT 0,
    odometer_km NUMERIC(12,2),
    kilometers_travelled_km NUMERIC(12,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'idle',
    is_moving BOOLEAN DEFAULT FALSE,
    last_latitude NUMERIC(10,6),
    last_longitude NUMERIC(10,6),
    last_location_ts TIMESTAMP,
    assigned_driver UUID,
    maintenance_due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_driver) REFERENCES fleet_drivers(id)
);

-- Create fleet_missions table  
CREATE TABLE fleet_missions (
    id UUID PRIMARY KEY,
    fleet_id UUID NOT NULL,
    mission_number VARCHAR(100) NOT NULL UNIQUE,
    driver_id UUID,
    truck_id UUID,
    status VARCHAR(20) DEFAULT 'planned',
    priority VARCHAR(20) DEFAULT 'normal',
    origin VARCHAR(500),
    destination VARCHAR(500),
    current_location JSONB,
    route_polyline TEXT,
    distance_total_m NUMERIC(12,2) DEFAULT 0,
    distance_remaining_m NUMERIC(12,2) DEFAULT 0,
    progress_pct NUMERIC(5,2) DEFAULT 0,
    speed_kmh NUMERIC(5,2),
    eta TIMESTAMP,
    cargo JSONB DEFAULT '{}',
    stops JSONB DEFAULT '[]',
    mission_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES fleet_drivers(id),
    FOREIGN KEY (truck_id) REFERENCES fleet_trucks(id)
);

-- Create indexes
CREATE INDEX idx_fleet_drivers_fleet_id ON fleet_drivers(fleet_id);
CREATE INDEX idx_fleet_drivers_email ON fleet_drivers(email);
CREATE INDEX idx_fleet_trucks_fleet_id ON fleet_trucks(fleet_id);
CREATE INDEX idx_fleet_trucks_plate ON fleet_trucks(plate);
CREATE INDEX idx_fleet_trucks_status ON fleet_trucks(status);
CREATE INDEX idx_fleet_missions_fleet_id ON fleet_missions(fleet_id);
CREATE INDEX idx_fleet_missions_driver ON fleet_missions(driver_id);
CREATE INDEX idx_fleet_missions_truck ON fleet_missions(truck_id);
CREATE INDEX idx_fleet_missions_status ON fleet_missions(status);
CREATE INDEX idx_fleet_missions_mission_number ON fleet_missions(mission_number);

-- Create remaining tables
CREATE TABLE fleet_mission_stops (
    id UUID PRIMARY KEY,
    mission_id UUID NOT NULL,
    stop_order INT,
    location_name VARCHAR(255),
    address VARCHAR(500),
    latitude NUMERIC(10,6),
    longitude NUMERIC(10,6),
    arrival_time TIMESTAMP,
    departure_time TIMESTAMP,
    stop_duration_minutes INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
);

CREATE TABLE fleet_mission_events (
    id UUID PRIMARY KEY,
    mission_id UUID NOT NULL,
    event_type VARCHAR(50),
    description TEXT,
    latitude NUMERIC(10,6),
    longitude NUMERIC(10,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
);

CREATE TABLE fleet_mission_disputes (
    id UUID PRIMARY KEY,
    mission_id UUID NOT NULL,
    dispute_type VARCHAR(50),
    description TEXT,
    resolution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
);

CREATE TABLE fleet_driver_performance_daily (
    id UUID PRIMARY KEY,
    driver_id UUID NOT NULL,
    date DATE NOT NULL,
    deliveries_count INT DEFAULT 0,
    on_time_count INT DEFAULT 0,
    late_count INT DEFAULT 0,
    harsh_braking_count INT DEFAULT 0,
    idling_minutes INT DEFAULT 0,
    fuel_efficiency_liters_per_100km NUMERIC(5,2),
    safety_score NUMERIC(5,2) DEFAULT 0,
    efficiency_score NUMERIC(5,2) DEFAULT 0,
    overall_score NUMERIC(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES fleet_drivers(id)
);

CREATE TABLE fleet_admin_audit_logs (
    id BIGINT PRIMARY KEY,
    admin_id UUID NOT NULL,
    action VARCHAR(50),
    resource_type VARCHAR(50),
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fleet_truck_locations (
    id UUID PRIMARY KEY,
    truck_id UUID NOT NULL,
    latitude NUMERIC(10,6),
    longitude NUMERIC(10,6),
    speed NUMERIC(5,2),
    accuracy NUMERIC(5,2),
    altitude NUMERIC(8,2),
    heading INT,
    timestamp BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (truck_id) REFERENCES fleet_trucks(id)
);
"""

# SQLite version
sqlite_sql = """
CREATE TABLE IF NOT EXISTS fleet_drivers (
    id TEXT PRIMARY KEY,
    fleet_id TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    email TEXT UNIQUE,
    license_number TEXT UNIQUE,
    license_state TEXT,
    hire_date DATE,
    status TEXT DEFAULT 'active',
    on_duty INTEGER DEFAULT 0,
    performance_mark REAL DEFAULT 0,
    deliveries_count INTEGER DEFAULT 0,
    last_active_at TIMESTAMP,
    achievements TEXT DEFAULT '{}',
    photo_url TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fleet_trucks (
    id TEXT PRIMARY KEY,
    fleet_id TEXT NOT NULL,
    truck_identifier TEXT NOT NULL,
    plate TEXT NOT NULL UNIQUE,
    vin TEXT UNIQUE,
    telematics_id TEXT,
    make TEXT,
    model TEXT,
    year INTEGER,
    fuel_capacity_liters REAL,
    fuel_consumed_liters REAL DEFAULT 0,
    odometer_km REAL,
    kilometers_travelled_km REAL DEFAULT 0,
    status TEXT DEFAULT 'idle',
    is_moving INTEGER DEFAULT 0,
    last_latitude REAL,
    last_longitude REAL,
    last_location_ts TIMESTAMP,
    assigned_driver TEXT,
    maintenance_due_date DATE,
    current_location TEXT,
    speed_kmh REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_driver) REFERENCES fleet_drivers(id)
);

CREATE TABLE IF NOT EXISTS fleet_missions (
    id TEXT PRIMARY KEY,
    fleet_id TEXT NOT NULL,
    mission_number TEXT NOT NULL UNIQUE,
    driver_id TEXT,
    truck_id TEXT,
    status TEXT DEFAULT 'planned',
    priority TEXT DEFAULT 'normal',
    origin TEXT,
    destination TEXT,
    current_location TEXT,
    route_polyline TEXT,
    distance_total_m REAL DEFAULT 0,
    distance_remaining_m REAL DEFAULT 0,
    progress_pct REAL DEFAULT 0,
    speed_kmh REAL,
    eta TIMESTAMP,
    cargo TEXT DEFAULT '{}',
    stops TEXT DEFAULT '[]',
    mission_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES fleet_drivers(id),
    FOREIGN KEY (truck_id) REFERENCES fleet_trucks(id)
);

CREATE TABLE IF NOT EXISTS fleet_mission_stops (
    id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    stop_order INTEGER,
    location_name TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL,
    arrival_time TIMESTAMP,
    departure_time TIMESTAMP,
    stop_duration_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
);

CREATE TABLE IF NOT EXISTS fleet_mission_events (
    id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    event_type TEXT,
    description TEXT,
    latitude REAL,
    longitude REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
);

CREATE TABLE IF NOT EXISTS fleet_mission_disputes (
    id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    dispute_type TEXT,
    description TEXT,
    resolution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
);

CREATE TABLE IF NOT EXISTS fleet_driver_performance_daily (
    id TEXT PRIMARY KEY,
    driver_id TEXT NOT NULL,
    date DATE NOT NULL,
    deliveries_count INTEGER DEFAULT 0,
    on_time_count INTEGER DEFAULT 0,
    late_count INTEGER DEFAULT 0,
    harsh_braking_count INTEGER DEFAULT 0,
    idling_minutes INTEGER DEFAULT 0,
    fuel_efficiency_liters_per_100km REAL,
    safety_score REAL DEFAULT 0,
    efficiency_score REAL DEFAULT 0,
    overall_score REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES fleet_drivers(id)
);

CREATE TABLE IF NOT EXISTS fleet_admin_audit_logs (
    id INTEGER PRIMARY KEY,
    admin_id TEXT NOT NULL,
    action TEXT,
    resource_type TEXT,
    resource_id TEXT,
    old_values TEXT,
    new_values TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fleet_truck_locations (
    id TEXT PRIMARY KEY,
    truck_id TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    speed REAL,
    accuracy REAL,
    altitude REAL,
    heading INTEGER,
    timestamp INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (truck_id) REFERENCES fleet_trucks(id)
);
"""

# Execute appropriate SQL based on database type
sql_to_run = sqlite_sql if db_vendor == 'sqlite' else postgresql_sql

try:
    with connection.cursor() as cursor:
        if db_vendor == 'sqlite':
            # SQLite needs individual statements
            for statement in sqlite_sql.split(';'):
                if statement.strip():
                    cursor.execute(statement)
        else:
            # PostgreSQL can handle multiple statements
            cursor.execute(postgresql_sql)
    
    connection.commit()
    print("\nSuccessfully created all v2 schema tables")
    
    # Verify tables exist
    if db_vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'fleet_%'")
            tables = cursor.fetchall()
    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE 'fleet_%'
            """)
            tables = cursor.fetchall()
    
    print(f"\nVerification: Found {len(tables)} fleet tables:")
    for (table,) in tables:
        print(f"  - {table}")
        
except Exception as e:
    print(f"\nERROR creating v2 tables: {e}")
    import traceback
    traceback.print_exc()

# Create FleetActivity table for audit trail
print("\nCreating FleetActivity table for audit trail...")

fleet_activity_sql_sqlite = """
CREATE TABLE IF NOT EXISTS fleet_activities (
    id TEXT PRIMARY KEY,
    fleet_id TEXT NOT NULL,
    truck_id TEXT,
    driver_id TEXT,
    mission_id TEXT,
    activity_type TEXT NOT NULL,
    activity_category TEXT,
    location_lat REAL,
    location_lon REAL,
    location_name TEXT,
    speed_kmh REAL,
    distance_m REAL,
    fuel_liters REAL,
    fuel_percentage REAL,
    alert_level TEXT,
    breach_type TEXT,
    violation_details TEXT,
    mission_status_before TEXT,
    mission_status_after TEXT,
    metadata TEXT,
    activity_date DATE,
    activity_time TIME,
    timestamp TIMESTAMP,
    is_critical BOOLEAN DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (truck_id) REFERENCES fleet_trucks(id),
    FOREIGN KEY (driver_id) REFERENCES fleet_drivers(id),
    FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
);

CREATE INDEX IF NOT EXISTS idx_fleet_activities_fleet_type_ts ON fleet_activities(fleet_id, activity_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_truck_date ON fleet_activities(truck_id, activity_date);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_driver_date ON fleet_activities(driver_id, activity_date);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_mission_ts ON fleet_activities(mission_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_category_ts ON fleet_activities(activity_category, timestamp);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_critical_ts ON fleet_activities(is_critical, timestamp);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_ts ON fleet_activities(timestamp);
"""

fleet_activity_sql_postgres = """
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

CREATE INDEX IF NOT EXISTS idx_fleet_activities_fleet_type_ts ON fleet_activities(fleet_id, activity_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_truck_date ON fleet_activities(truck_id, activity_date);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_driver_date ON fleet_activities(driver_id, activity_date);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_mission_ts ON fleet_activities(mission_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_category_ts ON fleet_activities(activity_category, timestamp);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_critical_ts ON fleet_activities(is_critical, timestamp);
CREATE INDEX IF NOT EXISTS idx_fleet_activities_ts ON fleet_activities(timestamp);
"""

try:
    with connection.cursor() as cursor:
        if db_vendor == 'sqlite':
            for statement in fleet_activity_sql_sqlite.split(';'):
                if statement.strip():
                    cursor.execute(statement)
        else:
            cursor.execute(fleet_activity_sql_postgres)
    
    connection.commit()
    print("✓ FleetActivity table and indexes created successfully")
    
except Exception as e:
    print(f"Warning: FleetActivity table creation failed (may already exist): {e}")

print("\nEmergency database setup complete")
