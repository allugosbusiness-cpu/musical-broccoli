"""
Management command to clear old api app migrations from the database
This must run BEFORE the main migrate command during deployment
"""
from django.core.management.base import BaseCommand
from django.db import connection, ProgrammingError


class Command(BaseCommand):
    help = 'Clear old api app migration history from database to allow fresh server.api migrations'

    def handle(self, *args, **options):
        """Delete all migration records for the deprecated 'api' app from the database"""
        try:
            with connection.cursor() as cursor:
                # First check if django_migrations table exists
                table_exists = False
                if connection.vendor == 'postgresql':
                    cursor.execute("""
                        SELECT EXISTS(
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' AND table_name = 'django_migrations'
                        )
                    """)
                    table_exists = cursor.fetchone()[0]
                elif connection.vendor == 'sqlite':
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name = 'django_migrations'
                    """)
                    table_exists = cursor.fetchone() is not None
                
                if not table_exists:
                    self.stdout.write(
                        self.style.WARNING('⚠️  django_migrations table does not exist yet (first run)')
                    )
                    return
                
                # Delete all old api app migration records (including api.deprecated)
                cursor.execute("DELETE FROM django_migrations WHERE app IN ('api', 'api.deprecated')")
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
        except ProgrammingError as e:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Could not check migrations table: {e}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Error clearing old migrations: {e}'
                )
            )
            # Don't raise - allow deployment to continue even if this fails
