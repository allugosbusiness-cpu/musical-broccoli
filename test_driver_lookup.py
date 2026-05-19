import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, '.')

django.setup()

from server.api.views import get_driver_by_id_or_name
from server.api.models import FleetDriver

# Get the actual driver
driver = FleetDriver.objects.first()
if driver:
    print(f'Driver name: {driver.first_name} {driver.last_name}')
    
    # Test 1: Look up by ID
    result = get_driver_by_id_or_name(str(driver.id))
    print(f'Lookup by ID: {result.first_name if result else "NOT FOUND"}')
    
    # Test 2: Look up by full name
    full_name = f'{driver.first_name} {driver.last_name}'
    result = get_driver_by_id_or_name(full_name)
    print(f'Lookup by name "{full_name}": {result.first_name if result else "NOT FOUND"}')
else:
    print('No drivers found')
