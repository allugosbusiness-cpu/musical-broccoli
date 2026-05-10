#!/usr/bin/env python
import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.models_v2 import FleetDriver

# Check if any drivers exist
drivers = FleetDriver.objects.all().values('fleet_id').distinct()[:5]
if drivers:
    print("Existing fleet_ids:")
    for d in drivers:
        print(f"  {d['fleet_id']}")
else:
    print("No drivers found.")
    
# Generate a default fleet_id for reference
default_fleet_id = uuid.uuid4()
print(f"\nA default fleet_id can be: {default_fleet_id}")
