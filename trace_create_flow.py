import os
import sys
import django
import json
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

print("="*70)
print("TRACING SERIALIZER CREATE FLOW")
print("="*70)

from server.api.serializers import MissionSerializer
from server.api.models import FleetTruck, FleetDriver

# Get actual truck and driver
truck = FleetTruck.objects.first()
driver = FleetDriver.objects.first()

print(f"\nUsing truck: {truck} (ID: {truck.id})")
print(f"Using driver: {driver} (ID: {driver.id})")

# Prepare data exactly like the API would
mission_data = {
    "mission_number": "DEBUG-TRACE-001",
    "status": "planned",
    "priority": "high",
    "truck": str(truck.id),
    "driver": str(driver.id),
    "origin": {
        "name": "Harare",
        "lat": -17.8252,
        "lon": 31.0335
    },
    "destination": {
        "name": "Bulawayo",
        "lat": -20.1551,
        "lon": 28.5679
    }
}

print(f"\nCreating serializer with data:")
print(json.dumps(mission_data, indent=2, default=str))

serializer = MissionSerializer(data=mission_data)

if serializer.is_valid():
    print(f"\n✓ Serializer is valid")
    print(f"Validated data before create:")
    for key in ['origin', 'destination', 'distance_total_m']:
        val = serializer.validated_data.get(key)
        print(f"  {key}: {val}")
    
    # Create the mission
    mission = serializer.save()
    
    print(f"\n✓ Mission created: {mission.id}")
    print(f"Mission data after save:")
    print(f"  distance_total_m: {mission.distance_total_m}")
    print(f"  origin: {mission.origin}")
    print(f"  destination: {mission.destination}")
    
    if float(mission.distance_total_m) == 0:
        print(f"\n❌ PROBLEM: distance_total_m is still 0 after save!")
        print(f"   The serializer.create() method likely NOT setting the distance")
    else:
        print(f"\n✓ SUCCESS: Distance was calculated and saved!")
        
else:
    print(f"\n❌ Serializer validation FAILED:")
    print(json.dumps(serializer.errors, indent=2))
