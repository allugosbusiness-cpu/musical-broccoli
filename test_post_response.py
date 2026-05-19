#!/usr/bin/env python
"""
Test mission POST response to ensure truck_name and driver_name are returned
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
import uuid

print("=" * 70)
print("TEST: POST /api/v1/missions/ Response")
print("=" * 70)

# Get or create test data
trucks = FleetTruck.objects.all()[:1]
drivers = FleetDriver.objects.all()[:1]

if not trucks or not drivers:
    print("Creating test truck and driver...")
    truck = FleetTruck.objects.create(
        truck_identifier="POST-TEST-TRUCK",
        plate="POSTTEST01"
    )
    driver = FleetDriver.objects.create(
        first_name="Post",
        last_name="Tester",
        email="posttest@example.com",
        phone_number="555-POST"
    )
else:
    truck = trucks[0]
    driver = drivers[0]

print(f"Using truck: {truck.truck_identifier} ({truck.id})")
print(f"Using driver: {driver.first_name} {driver.last_name} ({driver.id})")

# Create mission via POST
client = Client()
payload = {
    "mission_number": f"POST-RESPONSE-TEST-{uuid.uuid4().hex[:8]}",
    "truck": str(truck.id),
    "driver": str(driver.id),
    "status": "planned",
    "origin": {
        "name": "Post Test Origin",
        "lat": -1.2921,
        "lng": 36.8219,
    },
    "destination": {
        "name": "Post Test Destination",
        "lat": -1.2850,
        "lng": 36.8270,
    },
    "priority": "high",
}

print(f"\n1. POST PAYLOAD:")
print(json.dumps(payload, indent=2))

response = client.post(
    '/api/v1/missions/',
    data=json.dumps(payload),
    content_type='application/json'
)

print(f"\n2. POST RESPONSE:")
print(f"Status: {response.status_code}")

if response.status_code in [200, 201]:
    try:
        result = json.loads(response.content)
        print(f"Response JSON:")
        # Pretty print with focus on key fields
        for key in ['id', 'mission_number', 'truck', 'truck_name', 'driver', 'driver_name', 'distance_total_m', 'status']:
            value = result.get(key)
            print(f"  {key}: {value}")
        
        # Check if truck_name and driver_name are present
        print(f"\n3. VERIFICATION:")
        has_truck_name = 'truck_name' in result
        has_driver_name = 'driver_name' in result
        truck_name_value = result.get('truck_name')
        driver_name_value = result.get('driver_name')
        
        print(f"  ✓ truck_name field present: {has_truck_name}")
        print(f"    Value: {truck_name_value}")
        print(f"  ✓ driver_name field present: {has_driver_name}")
        print(f"    Value: {driver_name_value}")
        
        if truck_name_value and driver_name_value:
            print(f"\n✅ SUCCESS: Both truck_name and driver_name are in response!")
        else:
            print(f"\n❌ ISSUE: truck_name or driver_name is missing or null!")
            print(f"Full response: {json.dumps(result, indent=2)}")
    except json.JSONDecodeError as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response.content}")
else:
    print(f"Error: {response.status_code}")
    print(f"Response: {response.content.decode('utf-8', errors='ignore')}")

print("\n" + "=" * 70)
