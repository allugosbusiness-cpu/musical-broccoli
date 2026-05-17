import os
import sys
import django
from pathlib import Path
from django.core.management import call_command

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')

try:
    django.setup()
    # We only run 'migrate'. The blueprints are now safely on GitHub.
    call_command('migrate', verbosity=0)
    print("✅ Database migrations applied successfully!")
except Exception as e:
    print(f"⚠️ Migration Note: {e}")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
