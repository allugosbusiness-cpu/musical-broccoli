#!/usr/bin/env python
"""
Test script to diagnose mission data saving and distance calculation issues
"""
import os
import sys
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

from django.test import Client
from server.api.models import FleetMission, FleetDriver, FleetTruck

print("=" * 70)
print("DIAGNOSTIC: Mission Data & Distance Calculation")
print("=" * 70)

# 1. Check recent missions in database
print("\n1. MISSIONS IN DATABASE:")
print("-" * 70)
missions = FleetMission.objects.all().order_by('-created_at')[:5]
if missions:
    for mission in missions:
        print(f"\nMission: {mission.mission_number}")
        print(f"  ID: {mission.id}")
        print(f"  Truck ID: {mission.truck_id}")
        print(f"  Truck Name: {mission.truck.truck_identifier if mission.truck else 'NULL'}")
        print(f"  Driver ID: {mission.driver_id}")
        print(f"  Driver Name: {mission.driver.first_name} {mission.driver.last_name if mission.driver else 'NULL'}")
        print(f"  Status: {mission.status}")
        print(f"  Origin: {mission.origin}")
        print(f"  Destination: {mission.destination}")
        print(f"  Distance (meters): {mission.distance_total_m}")
        print(f"  Created: {mission.created_at}")
else:
    print("No missions found in database!")

# 2. Test the API response for missions
print("\n\n2. API RESPONSE (via Django Test Client):")
print("-" * 70)
client = Client()
response = client.get('/api/v1/missions/')
print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")

if response.status_code == 200:
    try:
        data = json.loads(response.content)
        if isinstance(data, list) and len(data) > 0:
            print(f"Found {len(data)} missions")
            # Show first 3 missions
            for i, mission in enumerate(data[:3]):
                print(f"\n  Mission {i+1}: {mission.get('mission_number')}")
                print(f"    truck: {mission.get('truck')}")
                print(f"    truck_name: {mission.get('truck_name')}")
                print(f"    driver: {mission.get('driver')}")
                print(f"    driver_name: {mission.get('driver_name')}")
                print(f"    distance_total_m: {mission.get('distance_total_m')}")
                print(f"    origin: {mission.get('origin')}")
                print(f"    destination: {mission.get('destination')}")
        else:
            print("Empty response or not a list")
    except json.JSONDecodeError:
        print(f"Response (not JSON): {response.content[:200]}")
else:
    print(f"Error: {response.content[:500]}")

# 3. Test dashboard missions endpoint
print("\n\n3. DASHBOARD MISSIONS ENDPOINT:")
print("-" * 70)
response = client.get('/api/v1/dashboard/missions/')
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    try:
        data = json.loads(response.content)
        if isinstance(data, list) and len(data) > 0:
            print(f"Found {len(data)} missions")
            for i, mission in enumerate(data[:3]):
                print(f"\n  Mission {i+1}: {mission.get('mission_number')}")
                print(f"    truck_name: {mission.get('truck_name')}")
                print(f"    driver_name: {mission.get('driver_name')}")
                print(f"    distance_total_m: {mission.get('distance_total_m')}")
        else:
            print("Empty response")
    except json.JSONDecodeError:
        print(f"Response (not JSON): {response.content[:200]}")
else:
    print(f"Error: {response.content}")

# 4. Check if serializer methods are working
print("\n\n4. SERIALIZER TEST:")
print("-" * 70)
from server.api.serializers import MissionSerializer
if missions:
    mission = missions[0]
    serializer = MissionSerializer(mission)
    data = serializer.data
    print(f"Serialized mission: {mission.mission_number}")
    print(f"  truck: {data.get('truck')}")
    print(f"  truck_name: {data.get('truck_name')}")
    print(f"  driver: {data.get('driver')}")
    print(f"  driver_name: {data.get('driver_name')}")
    print(f"  distance_total_m: {data.get('distance_total_m')}")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
