import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

# Query missions and drivers
from server.api.models import FleetMission, FleetDriver, FleetTruck

print("=== DRIVERS ===")
drivers = FleetDriver.objects.all()
for d in drivers:
    print(f"Driver ID: {d.id}")
    print(f"  Name: {d.first_name} {d.last_name}")
    print(f"  Phone: {d.phone_number}")
    print(f"  Status: {d.status}")
    if d.truck:
        print(f"  Truck: {d.truck.truck_identifier}")
    print()

print("=== MISSIONS ===")
missions = FleetMission.objects.all()
for m in missions:
    print(f"Mission ID: {m.id}")
    print(f"  Number: {m.mission_number}")
    print(f"  Status: {m.status}")
    print(f"  Driver: {m.driver.first_name if m.driver else 'Not assigned'}")
    print(f"  Distance: {m.distance_total_m}m")
    print()

if missions.count() == 0:
    print("No missions found in database")
if drivers.count() == 0:
    print("No drivers found in database")
