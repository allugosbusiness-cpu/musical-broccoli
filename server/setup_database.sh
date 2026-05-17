#!/bin/bash
# Railway Database Setup Script for PulseTrack

echo "🔧 PulseTrack Railway Database Setup"
echo "===================================="

# Check if we're on Railway
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set! Make sure PostgreSQL plugin is added."
    exit 1
fi

echo "✅ DATABASE_URL found"

# Run migrations
echo "🔄 Running Django migrations..."
python manage.py migrate

# Create superuser (non-interactive)
echo "👤 Creating superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("✅ Superuser 'admin' created")
else:
    print("⚠️  Superuser already exists")
EOF

# Load sample data
echo "📊 Loading sample data..."
python manage.py add_sample_data.py 2>/dev/null || echo "⚠️  Sample data script not found"

echo "✅ Database setup complete!"
