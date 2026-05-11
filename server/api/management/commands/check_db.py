"""
Debug command to check database connection and table status
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Debug database connection and verify FleetActivity table'

    def handle(self, *args, **options):
        db_vendor = connection.vendor
        db_name = connection.settings_dict.get('NAME', 'unknown')
        
        self.stdout.write(f"Database vendor: {db_vendor}")
        self.stdout.write(f"Database name: {db_name}")
        
        # List all tables
        with connection.cursor() as cursor:
            if db_vendor == 'postgresql':
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
            else:
                cursor.execute("""
                    SELECT name FROM sqlite_master WHERE type='table'
                """)
            
            tables = cursor.fetchall()
            self.stdout.write(f"\nTables in database ({len(tables)}):")
            for (table,) in tables:
                self.stdout.write(f"  - {table}")
        
        # Check if FleetActivity exists
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT COUNT(*) FROM fleet_activities")
                count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"\nFleetActivity table exists with {count} records"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\nFleetActivity table NOT found: {e}"))
