"""
WSGI config for Logistics project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
import django

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')

# Initialize Django
django.setup()

# Ensure v2 schema tables exist (emergency fix for migration state issues)
def ensure_database_tables():
    """Create v2 schema tables if they don't exist - handles migration state issues"""
    try:
        from django.db import connection
        from api.models_v2 import FleetDriver
        
        # Quick check: try to query fleet_drivers
        FleetDriver.objects.count()
        return  # Tables exist, no action needed
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'no such table' not in error_msg and 'does not exist' not in error_msg:
            return  # Different error, don't try to fix
        
        # Tables don't exist - create them using raw SQL
        try:
            from django.db import connection
            
            with connection.cursor() as cursor:
                # Create fleet_drivers table
                if connection.vendor == 'sqlite':
                    cursor.execute("""
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
                        )
                    """)
                    cursor.execute("""
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
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (assigned_driver) REFERENCES fleet_drivers(id)
                        )
                    """)
                    cursor.execute("""
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
                        )
                    """)
                    cursor.execute("""
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
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS fleet_mission_events (
                            id TEXT PRIMARY KEY,
                            mission_id TEXT NOT NULL,
                            event_type TEXT,
                            description TEXT,
                            latitude REAL,
                            longitude REAL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS fleet_mission_disputes (
                            id TEXT PRIMARY KEY,
                            mission_id TEXT NOT NULL,
                            dispute_type TEXT,
                            description TEXT,
                            resolution TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
                        )
                    """)
                    cursor.execute("""
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
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS fleet_admin_audit_logs (
                            id INTEGER PRIMARY KEY,
                            admin_id TEXT NOT NULL,
                            action TEXT,
                            resource_type TEXT,
                            resource_id TEXT,
                            old_values TEXT,
                            new_values TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    cursor.execute("""
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
                        )
                    """)
                
                connection.commit()
                print("[WSGI] Emergency: Fleet tables created successfully")
                
        except Exception as create_error:
            print(f"[WSGI] Error creating emergency tables: {create_error}")

try:
    ensure_database_tables()
except Exception as e:
    print(f"[WSGI] Warning during database check: {e}")

application = get_wsgi_application()
