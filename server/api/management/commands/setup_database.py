"""
Django management command to initialize the Railway database
Run this on Railway: railway run python manage.py setup_database
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Initialize Railway database with migrations and sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 PulseTrack Railway Database Setup'))
        self.stdout.write('=' * 50)

        # Check DATABASE_URL
        if not os.environ.get('DATABASE_URL'):
            self.stdout.write(self.style.ERROR('❌ DATABASE_URL not set!'))
            return

        self.stdout.write(self.style.SUCCESS('✅ DATABASE_URL found'))

        # Run migrations
        self.stdout.write(self.style.WARNING('🔄 Running Django migrations...'))
        from django.core.management import call_command
        try:
            call_command('migrate')
            self.stdout.write(self.style.SUCCESS('✅ Migrations completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Migration error: {str(e)}'))
            return

        # Create superuser
        self.stdout.write(self.style.WARNING('👤 Creating superuser...'))
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS("✅ Superuser 'admin' created (password: admin123)"))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Superuser already exists'))

        # Load sample data
        self.stdout.write(self.style.WARNING('📊 Loading sample data...'))
        try:
            call_command('shell', stdin=open('add_sample_data.py'))
            self.stdout.write(self.style.SUCCESS('✅ Sample data loaded'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Sample data error: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('✅ Database setup complete!'))
