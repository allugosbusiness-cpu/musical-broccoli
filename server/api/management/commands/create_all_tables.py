"""
Management command to forcefully create all required tables
"""
from django.core.management.base import BaseCommand
from django.db import connection
import sys


class Command(BaseCommand):
    help = 'Forcefully create all required tables including FleetActivity'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*60)
        self.stdout.write("FORCE CREATE TABLES COMMAND")
        self.stdout.write("="*60 + "\n")
        
        db_vendor = connection.vendor
        self.stdout.write(f"Database: {db_vendor}")
        
        if db_vendor != 'postgresql':
            self.stdout.write(self.style.WARNING("Not PostgreSQL, skipping"))
            return
        
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
            self.stdout.write(self.style.SUCCESS("OK - FleetActivity table created successfully"))
            
            # Verify
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM fleet_activities")
                count = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(f"OK - Verified: {count} records in table"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"WARNING: {e}"))
