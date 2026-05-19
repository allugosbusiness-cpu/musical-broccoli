#!/usr/bin/env python
import os
import sys
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

from django.test import Client
from server.api.models import FleetDriver, FleetMission

# Get test data
print("=" * 60)
print("FINDING VALID TEST DATA")
print("=" * 60)

driver = FleetDriver.objects.first()
mission = FleetMission.objects.first()

if not driver:
    print("✗ No drivers found in database")
    sys.exit(1)

if not mission:
    print("✗ No missions found in database")
    sys.exit(1)

print(f"✓ Found driver: {driver.id}")
print(f"✓ Found mission: {mission.id}")

# Test the endpoint
print("\n" + "=" * 60)
print("TESTING mobile_mission_start_tracking ENDPOINT")
print("=" * 60)

client = Client()
url = '/api/v1/mobile/mission/start-tracking/'
payload = {
    'driver_id': str(driver.id),
    'mission_id': str(mission.id)
}

print(f"\nURL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print(f"\nSending POST request...")

response = client.post(url, data=json.dumps(payload), content_type='application/json')

print(f"\n✓ Status Code: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type', 'Not set')}")

if response.status_code == 200:
    try:
        data = json.loads(response.content)
        print(f"\n✓✓✓ SUCCESS! Response:")
        print(json.dumps(data, indent=2))
        print(f"\n✓ Mission status updated to: {data.get('mission', {}).get('status')}")
    except json.JSONDecodeError:
        print(f"Response (not JSON): {response.content[:200]}")
else:
    print(f"\n✗ ERROR {response.status_code}")
    print(f"Response: {response.content[:500].decode('utf-8', errors='ignore')}")

# Also test OPTIONS to see allowed methods
print("\n" + "=" * 60)
print("TESTING OPTIONS REQUEST")
print("=" * 60)
options_response = client.options(url)
print(f"OPTIONS Status: {options_response.status_code}")
print(f"Allow Header: {options_response.get('Allow', 'Not set')}")
