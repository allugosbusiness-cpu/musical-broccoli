import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, '.')

django.setup()

# Read the current views.py
with open('server/api/views.py', 'r') as f:
    content = f.read()

# Replace the try-except block to handle ValidationError
new_function = '''def get_driver_by_id_or_name(driver_identifier):
    """
    Get driver by UUID (ID) or by full name.
    Tries UUID first, then falls back to name lookup.
    Returns driver or None.
    """
    from django.core.exceptions import ValidationError
    try:
        # Try UUID first
        return FleetDriver.objects.get(id=driver_identifier)
    except (FleetDriver.DoesNotExist, ValueError, ValidationError):
        # Not a valid UUID, try name lookup
        # Split name into first and last name (simplistic: assumes "First Last" format)
        name_parts = driver_identifier.strip().split(maxsplit=1)
        if len(name_parts) == 2:
            first_name, last_name = name_parts
            try:
                return FleetDriver.objects.get(first_name__iexact=first_name, last_name__iexact=last_name)
            except FleetDriver.DoesNotExist:
                return None
        return None'''

# Find and replace the function
import re
pattern = r'def get_driver_by_id_or_name\(driver_identifier\):.*?(?=\n(?:class|def|\Z))'
content = re.sub(pattern, new_function, content, flags=re.DOTALL)

with open('server/api/views.py', 'w') as f:
    f.write(content)

print("Fixed get_driver_by_id_or_name to catch ValidationError")
