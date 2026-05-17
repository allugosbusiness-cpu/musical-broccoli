#!/usr/bin/env python
"""
Direct database migration script for Railway PostgreSQL
This bypasses the Railway CLI and connects directly to PostgreSQL
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import call_command

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

print("🔧 PulseTrack Railway Database Migration Script")
print("=" * 60)

# Check if DATABASE_URL is set
db_url = os.environ.get('DATABASE_URL')
if db_url:
    print(f"✅ DATABASE_URL found: {db_url[:50]}...")
else:
    print("⚠️  DATABASE_URL not set (using default database)")

try:
    # Run migrations
    print("\n🔄 Running Django migrations...")
    call_command('migrate', verbosity=2)
    print("✅ Migrations completed successfully")
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)

try:
    # Create superuser
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    print("\n👤 Creating superuser...")
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("✅ Superuser 'admin' created (password: admin123)")
    else:
        print("⚠️  Superuser 'admin' already exists")
except Exception as e:
    print(f"❌ Superuser creation failed: {e}")

try:
    # Load sample data if available
    print("\n📊 Checking for sample data...")
    if os.path.exists('add_sample_data.py'):
        print("⏳ Loading sample data...")
        import add_sample_data  # Will auto-execute if it has main code
        print("✅ Sample data loaded")
    else:
        print("⚠️  add_sample_data.py not found (skipping)")
except Exception as e:
    print(f"⚠️  Could not load sample data: {e}")

print("\n" + "=" * 60)
print("✅ Database initialization complete!")
print("\n📋 Next steps:")
print("1. Visit: https://musical-broccoli-production.up.railway.app/admin")
print("2. Login with: admin / admin123")
print("3. Test API: https://musical-broccoli-production.up.railway.app/api/v1/trucks/")
