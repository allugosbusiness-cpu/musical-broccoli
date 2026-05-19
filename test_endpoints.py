#!/usr/bin/env python
import os
import sys
import django
import json
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

# Enable Django logging to see errors
logging.basicConfig(level=logging.DEBUG)

from django.test import Client
from server.api.models import FleetDriver, FleetTruck

client = Client()

print('=' * 60)
print('TESTING BACKEND ENDPOINTS LOCALLY')
print('=' * 60)

# Test 1: Dashboard missions
print('\n1. Testing /api/v1/dashboard/missions/')
try:
    response = client.get('/api/v1/dashboard/missions/')
    print(f'   Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'   Missions count: {len(data)}')
    else:
        print(f'   Error: {response.content.decode()[:300]}')
except Exception as e:
    print(f'   Exception: {str(e)[:300]}')

# Test 2: Current mission with driver name
print('\n2. Testing /api/v1/mobile/driver/{{driver_name}}/current-mission/')
driver = FleetDriver.objects.first()
if driver:
    driver_name = f'{driver.first_name} {driver.last_name}'
    from urllib.parse import quote
    encoded_name = quote(driver_name)
    try:
        response = client.get(f'/api/v1/mobile/driver/{encoded_name}/current-mission/')
        print(f'   Driver: {driver_name}')
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print(f'   Has mission: {"mission" in data}')
        else:
            data = response.json()
            print(f'   Response: {data}')
    except Exception as e:
        print(f'   Exception: {str(e)[:300]}')
else:
    print('   No drivers found')

# Test 3: Truck trail
print('\n3. Testing /api/v1/trucks/{{truck_id}}/truck_trail_with_directions/')
truck = FleetTruck.objects.first()
if truck:
    truck_id = str(truck.id)
    try:
        response = client.get(f'/api/v1/trucks/{truck_id}/truck_trail_with_directions/?limit=100')
        print(f'   Truck ID: {truck_id}')
        print(f'   Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print(f'   Trail points: {data.get("count", 0)}')
        else:
            print(f'   Error: {response.content.decode()[:300]}')
    except Exception as e:
        print(f'   Exception: {str(e)[:300]}')
else:
    print('   No trucks found')

print('\n' + '=' * 60)
print('TESTS COMPLETE')
print('=' * 60)
