#!/usr/bin/env python
"""
Create a Django migration to fix missing columns
"""
import os
import sys
import django
from datetime import datetime

# Add server directory to path
sys.path.append('c:\\Users\\Mugogo\\Desktop\musical-broccoli-main\\server')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import migrations, models
import django.db.migrations.operations.fields

print("=== Creating Migration Fix ===")

# Create a new migration file
migration_content = '''"""
Migration: Add missing columns to fleet_missions table for Render deployment.
This migration handles the case where the database schema doesn't include
max_speed, avg_speed, and compressed_trail columns that are defined in the model.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_add_missing_optional_fields'),
    ]

    operations = [
        migrations.RunSQL(
            """
            -- Add missing columns if they don't exist
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'fleet_missions' AND column_name = 'max_speed') THEN
                    ALTER TABLE fleet_missions ADD COLUMN max_speed numeric(6,2) NOT NULL DEFAULT 0;
                    RAISE NOTICE 'Added max_speed column';
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'fleet_missions' AND column_name = 'avg_speed') THEN
                    ALTER TABLE fleet_missions ADD COLUMN avg_speed numeric(6,2) NOT NULL DEFAULT 0;
                    RAISE NOTICE 'Added avg_speed column';
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'fleet_missions' AND column_name = 'compressed_trail') THEN
                    ALTER TABLE fleet_missions ADD COLUMN compressed_trail jsonb NOT NULL DEFAULT '[]';
                    RAISE NOTICE 'Added compressed_trail column';
                END IF;
            END $$;
            """,
            reverse_sql=migrations.operations.fields.ReverseDropField()
        ),
    ]
'''

# Write the migration file
migration_filename = f"0003_fix_render_deployment.py"
migration_path = "server/api/migrations/" + migration_filename

try:
    with open(migration_path, 'w') as f:
        f.write(migration_content)
    print(f"✓ Created migration file: {migration_path}")
    
    print("\n=== Migration Content ===")
    print(migration_content)
    
    print("\n=== Next Steps ===")
    print("1. Copy this migration file to your Render deployment")
    print("2. Run: python manage.py migrate api")
    print("3. Test mission creation through web app")
    
    print("\n=== Alternative: Manual Migration Creation ===")
    print("If the above doesn't work, you can create the migration manually:")
    print("1. In your Render deployment, run:")
    print("   python manage.py makemigrations api --name fix_render_deployment")
    print("2. Then run:")
    print("   python manage.py migrate api")
    
except Exception as e:
    print(f"Error creating migration file: {e}")

print("\n=== Emergency Fix Approach ===")
print("If migrations still don't work, we can modify the model to be more flexible:")
print("1. Make fields truly optional with null=True")
print("2. Use database schema detection in the model manager")
print("3. Handle missing columns gracefully at runtime")