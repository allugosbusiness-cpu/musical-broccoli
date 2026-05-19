#!/usr/bin/env python
"""
Quick verification test after serializer fix
"""
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

from django.test import Client
from server.api.models import FleetDriver, FleetTruck
from decimal import Decimal

print("=" * 70)
print("VERIFICATION: Mission Creation with Proper Serialization")
print("=" * 70)

client = Client()

# Get test data
trucks = list(FleetTruck.objects.all())[:1]
drivers = list(FleetDriver.objects.all())[:1]

if trucks and drivers:
    truck = trucks[0]
    driver = drivers[0]
    
    print(f"\n1. Creating mission with:")
    print(f"   Truck: {truck.truck_identifier} ({truck.id})")
    print(f"   Driver: {driver.first_name} {driver.last_name} ({driver.id})")
    
    payload = {
        "mission_number": f"VERIFY-{truck.id.hex[:8]}",
        "truck": str(truck.id),
        "driver": str(driver.id),
        "status": "planned",
        "origin": {
            "name": "Verify Origin",
            "lat": -1.2921,
            "lng": 36.8219,
        },
        "destination": {
            "name": "Verify Destination",
            "lat": -1.2850,
            "lng": 36.8270,
        },
        "priority": "normal",
    }
    
    response = client.post(
        '/api/v1/missions/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    print(f"\n2. POST Response Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = json.loads(response.content)
        
        print(f"\n3. Response Fields:")
        print(f"   mission_number: {result.get('mission_number')}")
        print(f"   truck_name: {result.get('truck_name')}")
        print(f"   driver_name: {result.get('driver_name')}")
        
        distance = result.get('distance_total_m')
        print(f"   distance_total_m: {distance} (type: {type(distance).__name__})")
        
        # Verify it's a number
        if isinstance(distance, (int, float)):
            distance_km = float(distance) / 1000
            print(f"   distance in km: {distance_km:.2f}km ✓")
        else:
            print(f"   ERROR: distance is not a number!")
        
        print(f"\n4. Summary:")
        if result.get('truck_name') and result.get('driver_name') and distance:
            print(f"   ✅ All fields populated correctly!")
        else:
            print(f"   ❌ Some fields are missing!")
            print(f"   Full response: {json.dumps(result, indent=2)}")
    else:
        print(f"   Error: {response.content.decode('utf-8', errors='ignore')}")
else:
    print("No test data available!")

print("\n" + "=" * 70)
