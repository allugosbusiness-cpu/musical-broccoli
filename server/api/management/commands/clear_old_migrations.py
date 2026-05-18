"""
Management command to clear old api app migrations from the database
This must run BEFORE the main migrate command during deployment
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Clear old api app migration history from database to allow fresh server.api migrations'

    def handle(self, *args, **options):
        """Delete all migration records for the deprecated 'api' app from the database"""
        try:
            with connection.cursor() as cursor:
                # Delete all old api app migration records
                cursor.execute("DELETE FROM django_migrations WHERE app = 'api'")
                deleted_count = cursor.rowcount
                
                if deleted_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Cleared {deleted_count} old api app migration record(s) from database'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️ No old api app migrations found to clear')
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Error clearing old migrations: {e}'
                )
            )
            raise
