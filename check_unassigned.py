#!/usr/bin/env python
"""
Check for missions with missing truck or driver
"""
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

from server.api.models import FleetMission
from django.test import Client

print("=" * 70)
print("CHECK: Missions with Missing Truck or Driver")
print("=" * 70)

# 1. Check database for unassigned missions
print("\n1. DATABASE: Missions with NULL truck or driver:")
print("-" * 70)

null_truck = FleetMission.objects.filter(truck__isnull=True)
null_driver = FleetMission.objects.filter(driver__isnull=True)

print(f"Missions with NULL truck: {null_truck.count()}")
for mission in null_truck[:5]:
    print(f"  {mission.mission_number} - driver: {mission.driver.first_name if mission.driver else 'NULL'}")

print(f"\nMissions with NULL driver: {null_driver.count()}")
for mission in null_driver[:5]:
    print(f"  {mission.mission_number} - truck: {mission.truck.truck_identifier if mission.truck else 'NULL'}")

# 2. Check ALL missions and their status
print("\n2. ALL MISSIONS AND ASSIGNMENT STATUS:")
print("-" * 70)
all_missions = FleetMission.objects.all().order_by('-created_at')[:10]
for mission in all_missions:
    truck_status = f"✓ {mission.truck.truck_identifier}" if mission.truck else "✗ NULL"
    driver_status = f"✓ {mission.driver.first_name}" if mission.driver else "✗ NULL"
    print(f"{mission.mission_number:20} | Truck: {truck_status:25} | Driver: {driver_status:20} | Status: {mission.status}")

# 3. Check what the API is returning for these missions
print("\n3. API RESPONSE CHECK:")
print("-" * 70)
client = Client()
response = client.get('/api/v1/dashboard/missions/')

if response.status_code == 200:
    missions_data = json.loads(response.content)
    print(f"Total missions from API: {len(missions_data)}")
    
    # Find missions with Unassigned
    unassigned = [m for m in missions_data if m.get('truck_name') is None or m.get('driver_name') is None]
    print(f"Missions with unassigned truck/driver: {len(unassigned)}")
    
    for m in unassigned[:5]:
        print(f"  {m.get('mission_number'):20} | truck_name: {m.get('truck_name')} | driver_name: {m.get('driver_name')}")

print("\n" + "=" * 70)
