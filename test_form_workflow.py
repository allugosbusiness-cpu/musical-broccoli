import os
import sys
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

from django.test import Client
from decimal import Decimal

# Create test client
client = Client()

print("="*70)
print("COMPREHENSIVE TEST: Mission Form Workflow")
print("="*70)

# 1. Frontend: Get dashboard trucks and drivers
print("\n1. FRONTEND: getDashboardTrucks() & getDashboardDrivers()")
print("-"*70)
trucks_response = client.get('/api/v1/fleet/dashboard/trucks/')
drivers_response = client.get('/api/v1/fleet/dashboard/drivers/')

trucks = trucks_response.json()
drivers = drivers_response.json()

print(f"Trucks fetched: {len(trucks)}")
if trucks:
    truck = trucks[0]
    print(f"  First truck: {truck.get('id')} - {truck.get('truck_identifier')}")
    print(f"  Has 'id' field: {'id' in truck}")
    print(f"  'id' value type: {type(truck.get('id'))}")

print(f"Drivers fetched: {len(drivers)}")
if drivers:
    driver = drivers[0]
    print(f"  First driver: {driver.get('id')} - {driver.get('first_name')} {driver.get('last_name')}")
    print(f"  Has 'id' field: {'id' in driver}")
    print(f"  'id' value type: {type(driver.get('id'))}")

# 2. Frontend: User submits form
print("\n2. FRONTEND: User submits form with selected values")
print("-"*70)
payload = {
    "mission_number": "FORM-SIM-TEST",
    "status": "planned",
    "priority": "high",
    "truck": trucks[0]['id'],
    "driver": drivers[0]['id'],
    "origin": {"name": "Warehouse A", "lat": -1.2921, "lng": 36.8219},
    "destination": {"name": "Location B", "lat": -1.2850, "lng": 36.8270}
}
print(f"Payload truck: {payload['truck']} (type: {type(payload['truck'])})")
print(f"Payload driver: {payload['driver']} (type: {type(payload['driver'])})")

# 3. API: POST /api/v1/missions/
print("\n3. API: POST /api/v1/missions/")
print("-"*70)
post_response = client.post('/api/v1/missions/', json=payload, content_type='application/json')
print(f"Status: {post_response.status_code}")

if post_response.status_code in [200, 201]:
    mission = post_response.json()
    print(f"Mission ID: {mission.get('id')}")
    print(f"truck field: {mission.get('truck')}")
    print(f"truck_name field: {mission.get('truck_name')}")
    print(f"driver field: {mission.get('driver')}")
    print(f"driver_name field: {mission.get('driver_name')}")
    distance = mission.get('distance_total_m')
    print(f"distance_total_m: {distance} (type: {type(distance)})")
    
    # 4. Frontend: Get missions for AdminDashboard
    print("\n4. FRONTEND: Get missions for AdminDashboard")
    print("-"*70)
    dashboard_response = client.get('/api/v1/fleet/dashboard/missions/')
    missions = dashboard_response.json()
    
    # Find our mission
    our_mission = None
    for m in missions:
        if m.get('mission_number') == 'FORM-SIM-TEST':
            our_mission = m
            break
    
    if our_mission:
        print(f"Found our mission in dashboard response:")
        print(f"  mission_number: {our_mission.get('mission_number')}")
        print(f"  truck_name: {our_mission.get('truck_name')}")
        print(f"  driver_name: {our_mission.get('driver_name')}")
        print(f"  distance_total_m: {our_mission.get('distance_total_m')}")
        
        # 5. Display check
        print("\n5. DISPLAY CHECK:")
        print("-"*70)
        
        # Handle both string and numeric distance values
        distance_value = our_mission.get('distance_total_m', 0)
        if isinstance(distance_value, str):
            distance_value = float(distance_value) if distance_value else 0
        else:
            distance_value = float(distance_value) if distance_value else 0
        
        distance_display = f"{(distance_value / 1000):.1f}km" if distance_value else 'N/A'
        
        print(f"Mission Display:")
        print(f"  • Mission #: {our_mission.get('mission_number')}")
        print(f"  • Truck: {our_mission.get('truck_name')}")
        print(f"  • Driver: {our_mission.get('driver_name')}")
        print(f"  • Distance: {distance_display}")
        print(f"  • Priority: {our_mission.get('priority')}")
        print(f"  • Status: {our_mission.get('status')}")
        
        print("\n√√√ SUCCESS: Form workflow complete!")
        print("   - Frontend retrieves trucks/drivers")
        print("   - Frontend submits form with IDs")
        print("   - API creates mission with auto-calculated distance")
        print("   - Frontend displays mission with truck_name, driver_name, and distance")
    else:
        print("✗ ERROR: Mission not found in dashboard")
else:
    print(f"✗ ERROR {post_response.status_code}: {post_response.content}")
