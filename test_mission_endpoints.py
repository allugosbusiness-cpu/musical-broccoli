#!/usr/bin/env python
"""
Test the mission endpoints locally
"""
import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Logistics.settings")
django.setup()

from rest_framework.test import APIRequestFactory
from api.mobile_endpoints import get_available_missions, start_mission_tracking
from api.models_v2 import FleetDriver, FleetTruck, FleetMission

# Get test driver/truck
driver_id = "570eb29f-ee89-4676-9d16-0fe7593ae8d8"

try:
    driver = FleetDriver.objects.get(id=driver_id)
    print(f"✅ Found driver: {driver.get_display_name()}")
except FleetDriver.DoesNotExist:
    print(f"❌ Driver not found: {driver_id}")
    exit(1)

# Test the endpoint
factory = APIRequestFactory()
request = factory.get(f'/api/v1/mobile/driver/{driver_id}/available-missions/')

response = get_available_missions(request, driver_id)
print(f"\n📋 get_available_missions endpoint:")
print(f"  Status: {response.status_code}")
print(f"  Data: {json.dumps(response.data, indent=2)}")

# Check missions in database
missions = FleetMission.objects.filter(truck=driver.truck, status__in=['planned', 'assigned'])
print(f"\n🎯 Missions in database for truck {driver.truck.truck_identifier}:")
print(f"  Count: {missions.count()}")
for m in missions:
    print(f"    - {m.mission_number} ({m.status})")
