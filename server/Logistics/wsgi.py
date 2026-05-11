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
    print("[WSGI] Starting database table check...")
    try:
        from django.db import connection
        from api.models_v2 import FleetDriver
        
        # Quick check: try to query fleet_drivers
        count = FleetDriver.objects.count()
        print(f"[WSGI] Tables already exist! Found {count} drivers")
        return  # Tables exist, no action needed
        
    except Exception as e:
        error_msg = str(e).lower()
        print(f"[WSGI] Database check failed: {e}")
        print(f"[WSGI] Error type: {type(e).__name__}")
        if 'no such table' not in error_msg and 'does not exist' not in error_msg and 'relation' not in error_msg:
            print(f"[WSGI] Not a table-missing error, skipping creation")
            return  # Different error, don't try to fix
        
        # Tables don't exist - create them using raw SQL
        print("[WSGI] Creating v2 schema tables...")
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
                    print("[WSGI] Emergency: SQLite fleet tables created successfully")
                else:
                    # PostgreSQL: Create all tables with proper data types
                    print("[WSGI] Creating PostgreSQL tables...")
                    
                    # PostgreSQL SQL with proper data types
                    pg_sql = """
                    CREATE TABLE IF NOT EXISTS fleet_drivers (
                        id VARCHAR(36) PRIMARY KEY,
                        fleet_id VARCHAR(36) NOT NULL,
                        first_name VARCHAR(100) NOT NULL,
                        last_name VARCHAR(100) NOT NULL,
                        phone VARCHAR(20),
                        phone_number VARCHAR(20) UNIQUE,
                        email VARCHAR(254) UNIQUE,
                        license_number VARCHAR(50) UNIQUE,
                        license_state VARCHAR(10),
                        hire_date DATE,
                        status VARCHAR(20) DEFAULT 'active',
                        on_duty BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        truck_id VARCHAR(36),
                        latitude NUMERIC(9,6),
                        longitude NUMERIC(9,6),
                        current_speed NUMERIC(6,2) DEFAULT 0,
                        last_location_update TIMESTAMP,
                        performance_mark NUMERIC(8,2) DEFAULT 0,
                        deliveries_count INTEGER DEFAULT 0,
                        last_active_at TIMESTAMP,
                        achievements TEXT DEFAULT '{}',
                        photo_url VARCHAR(500),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE TABLE IF NOT EXISTS fleet_trucks (
                        id VARCHAR(36) PRIMARY KEY,
                        fleet_id VARCHAR(36) NOT NULL,
                        truck_identifier VARCHAR(100) NOT NULL UNIQUE,
                        plate VARCHAR(20) NOT NULL UNIQUE,
                        vin VARCHAR(50) UNIQUE,
                        telematics_id VARCHAR(100) UNIQUE,
                        make VARCHAR(100),
                        model VARCHAR(100),
                        year INTEGER,
                        fuel_capacity_liters NUMERIC(10,2) DEFAULT 100,
                        fuel_consumed_liters NUMERIC(10,2) DEFAULT 0,
                        odometer_km NUMERIC(12,2) DEFAULT 0,
                        kilometers_travelled_km NUMERIC(12,2) DEFAULT 0,
                        status VARCHAR(20) DEFAULT 'idle',
                        is_moving BOOLEAN DEFAULT FALSE,
                        last_latitude NUMERIC(9,6),
                        last_longitude NUMERIC(9,6),
                        last_location_ts TIMESTAMP,
                        assigned_driver VARCHAR(36),
                        maintenance_due_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (assigned_driver) REFERENCES fleet_drivers(id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS fleet_missions (
                        id VARCHAR(36) PRIMARY KEY,
                        fleet_id VARCHAR(36) NOT NULL,
                        mission_number VARCHAR(100) NOT NULL UNIQUE,
                        driver_id VARCHAR(36),
                        truck_id VARCHAR(36),
                        status VARCHAR(20) DEFAULT 'planned',
                        priority VARCHAR(20) DEFAULT 'normal',
                        origin VARCHAR(500),
                        destination VARCHAR(500),
                        current_location TEXT,
                        route_polyline TEXT,
                        distance_total_m NUMERIC(12,2) DEFAULT 0,
                        distance_remaining_m NUMERIC(12,2) DEFAULT 0,
                        progress_pct NUMERIC(5,2) DEFAULT 0,
                        speed_kmh NUMERIC(5,2),
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
                        id VARCHAR(36) PRIMARY KEY,
                        mission_id VARCHAR(36) NOT NULL,
                        stop_order INTEGER,
                        location_name VARCHAR(255),
                        address VARCHAR(500),
                        latitude NUMERIC(10,6),
                        longitude NUMERIC(10,6),
                        arrival_time TIMESTAMP,
                        departure_time TIMESTAMP,
                        stop_duration_minutes INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS fleet_mission_events (
                        id VARCHAR(36) PRIMARY KEY,
                        mission_id VARCHAR(36) NOT NULL,
                        event_type VARCHAR(50),
                        description TEXT,
                        latitude NUMERIC(10,6),
                        longitude NUMERIC(10,6),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS fleet_mission_disputes (
                        id VARCHAR(36) PRIMARY KEY,
                        mission_id VARCHAR(36) NOT NULL,
                        dispute_type VARCHAR(50),
                        description TEXT,
                        resolution TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (mission_id) REFERENCES fleet_missions(id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS fleet_driver_performance_daily (
                        id VARCHAR(36) PRIMARY KEY,
                        driver_id VARCHAR(36) NOT NULL,
                        date DATE NOT NULL,
                        deliveries_count INTEGER DEFAULT 0,
                        on_time_count INTEGER DEFAULT 0,
                        late_count INTEGER DEFAULT 0,
                        harsh_braking_count INTEGER DEFAULT 0,
                        idling_minutes INTEGER DEFAULT 0,
                        fuel_efficiency_liters_per_100km NUMERIC(5,2),
                        safety_score NUMERIC(5,2) DEFAULT 0,
                        efficiency_score NUMERIC(5,2) DEFAULT 0,
                        overall_score NUMERIC(5,2) DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (driver_id) REFERENCES fleet_drivers(id)
                    );
                    
                    CREATE TABLE IF NOT EXISTS fleet_admin_audit_logs (
                        id BIGINT PRIMARY KEY,
                        admin_id VARCHAR(36) NOT NULL,
                        action VARCHAR(50),
                        resource_type VARCHAR(50),
                        resource_id VARCHAR(36),
                        old_values TEXT,
                        new_values TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE TABLE IF NOT EXISTS fleet_truck_locations (
                        id VARCHAR(36) PRIMARY KEY,
                        truck_id VARCHAR(36) NOT NULL,
                        latitude NUMERIC(10,6),
                        longitude NUMERIC(10,6),
                        speed NUMERIC(5,2),
                        accuracy NUMERIC(5,2),
                        altitude NUMERIC(8,2),
                        heading INTEGER,
                        timestamp BIGINT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (truck_id) REFERENCES fleet_trucks(id)
                    );
                    """
                    
                    # Execute PostgreSQL statements
                    cursor.execute(pg_sql)
                    connection.commit()
                    print("[WSGI] Emergency: PostgreSQL fleet tables created successfully")
                
        except Exception as create_error:
            print(f"[WSGI] Error creating emergency tables: {create_error}")

try:
    ensure_database_tables()
except Exception as e:
    print(f"[WSGI] Warning during database check: {e}")

# Seed initial data if tables are empty
def ensure_initial_data():
    """Ensure database has initial test data"""
    try:
        from api.models_v2 import FleetDriver, FleetTruck
        
        # Check if we already have data
        if FleetDriver.objects.exists() and FleetTruck.objects.exists():
            return
        
        print("[WSGI] Seeding initial database data...")
        import uuid
        from datetime import datetime
        from django.db import transaction
        
        with transaction.atomic():
            # Create drivers
            drivers = []
            driver_data = [
                {'first_name': 'John', 'last_name': 'Driver', 'email': 'john.driver@example.com'},
                {'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane.smith@example.com'},
            ]
            
            for data in driver_data:
                driver, _ = FleetDriver.objects.get_or_create(
                    email=data['email'],
                    defaults={
                        'id': str(uuid.uuid4()),
                        'fleet_id': str(uuid.uuid4()),
                        'first_name': data['first_name'],
                        'last_name': data['last_name'],
                        'status': 'active',
                        'on_duty': True,
                        'is_active': True,
                    }
                )
                drivers.append(driver)
            
            # Create trucks
            trucks_data = [
                {
                    'truck_identifier': 'trk2',
                    'plate': 'ZWE-1001',
                    'make': 'Volvo',
                    'model': 'FH16',
                    'year': 2020,
                    'fuel_capacity_liters': 500,
                    'status': 'idle',
                    'is_moving': False,
                    'last_latitude': -17.8252,
                    'last_longitude': 31.0335,
                },
                {
                    'truck_identifier': 'trk3',
                    'plate': 'ATY 3272',
                    'make': 'Mercedes',
                    'model': 'Actros',
                    'year': 2021,
                    'fuel_capacity_liters': 600,
                    'status': 'enroute',
                    'is_moving': True,
                    'last_latitude': -17.8256,
                    'last_longitude': 31.0345,
                },
                {
                    'truck_identifier': 'trk4',
                    'plate': 'AQW7645',
                    'make': 'Hino',
                    'model': '500',
                    'year': 2019,
                    'fuel_capacity_liters': 400,
                    'status': 'idle',
                    'is_moving': False,
                    'last_latitude': -17.8260,
                    'last_longitude': 31.0340,
                },
                {
                    'truck_identifier': 'TRK1',
                    'plate': 'AXE5422',
                    'make': 'Scania',
                    'model': 'R500',
                    'year': 2022,
                    'fuel_capacity_liters': 550,
                    'status': 'idle',
                    'is_moving': False,
                    'last_latitude': -17.8250,
                    'last_longitude': 31.0330,
                },
            ]
            
            trucks = []
            for i, data in enumerate(trucks_data):
                truck, _ = FleetTruck.objects.get_or_create(
                    plate=data['plate'],
                    defaults={
                        'id': str(uuid.uuid4()),
                        'fleet_id': str(uuid.uuid4()),
                        'assigned_driver': drivers[i % len(drivers)] if drivers else None,
                        **data
                    }
                )
                trucks.append(truck)
            
            print(f"[WSGI] Seeded {len(drivers)} drivers and {len(trucks)} trucks")
            
    except Exception as e:
        print(f"[WSGI] Note: Could not seed data (may already exist): {e}")

try:
    ensure_initial_data()
except Exception as e:
    print(f"[WSGI] Warning during data seeding: {e}")

application = get_wsgi_application()
