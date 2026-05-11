#!/usr/bin/env python
"""
Fix migration issues by clearing and reapplying migrations
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

print("Fixing migrations...")

# Clear all migrations for the api app
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'api'")
    print("Cleared api migrations from django_migrations table")

# Run migrations again
print("Reapplying migrations...")
try:
    call_command('migrate', 'api', verbosity=2)
    print("Migrations applied successfully")
except Exception as e:
    print(f"Error applying migrations: {e}")
    import traceback
    traceback.print_exc()
