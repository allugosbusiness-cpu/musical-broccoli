#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.models_v2 import FleetTruck
from uuid import uuid4
from decimal import Decimal
from django.utils import timezone

# Try to create a test truck
try:
    print("Creating test truck...")
    truck = FleetTruck.objects.create(
        fleet_id=str(uuid4()),
        truck_identifier='BACKEND-TEST-001',
        plate='BTEST-001',
        make='Toyota',
        model='Hiace',
        status='IDLE',
        last_latitude=Decimal('-17.8252'),
        last_longitude=Decimal('31.0335'),
        last_location_ts=timezone.now()
    )
    print(f'✅ Truck created: {truck.id} - {truck.truck_identifier}')
    
    # Query it back
    retrieved = FleetTruck.objects.get(id=truck.id)
    print(f'✅ Retrieved truck: {retrieved.truck_identifier}')
    print(f'✅ All trucks count: {FleetTruck.objects.count()}')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
