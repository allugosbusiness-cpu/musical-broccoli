import os
import sys
import django
from pathlib import Path
from django.core.management import call_command
from django.db import connection

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')

try:
    django.setup()
    
    # Clear any old migration history for the deprecated 'api' app
    with connection.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'api'")
            print("✅ Cleared old api app migration history")
        except Exception as e:
            print(f"⚠️ Could not clear old api migrations: {e}")
    
    # Apply migrations only for the new server.api app
    call_command('migrate', 'server', verbosity=1)
    print("✅ Database migrations applied successfully!")
except Exception as e:
    print(f"⚠️ Migration error: {e}")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
