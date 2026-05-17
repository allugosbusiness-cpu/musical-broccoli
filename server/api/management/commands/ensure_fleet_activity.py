"""
Management command to ensure FleetActivity table exists
"""
from django.core.management.base import BaseCommand
from django.db import connection, migrations
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = 'Ensure FleetActivity table exists by running migrations'

    def handle(self, *args, **options):
        self.stdout.write("Checking FleetActivity table...")
        
        # Check if table exists
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT 1 FROM fleet_activities LIMIT 1")
                self.stdout.write(self.style.SUCCESS("✓ FleetActivity table exists"))
                return
            except Exception as e:
                self.stdout.write(f"Table check failed: {e}")
        
        # Run migrations
        self.stdout.write("Running migrations...")
        executor = MigrationExecutor(connection)
        executor.migrate([('api', None)])
        
        # Verify table now exists
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT 1 FROM fleet_activities LIMIT 1")
                self.stdout.write(self.style.SUCCESS("✓ FleetActivity table created via migrations"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to create table: {e}"))
                raise
