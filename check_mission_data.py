import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.models_v2 import FleetMission

missions = FleetMission.objects.all()
print(f"Total missions: {missions.count()}")

for m in missions:
    print(f"\n=== Mission {m.mission_number} ===")
    print(f"Origin: {m.origin}")
    print(f"Destination: {m.destination}")
    print(f"Current Location: {m.current_location}")
    print(f"Status: {m.status}")
    print(f"Truck: {m.truck.truck_identifier if m.truck else 'None'}")
