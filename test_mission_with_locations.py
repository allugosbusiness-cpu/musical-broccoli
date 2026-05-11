#!/usr/bin/env python
"""Test mission creation with location suggestions"""

import requests
import json

BASE_URL = 'https://musical-broccoli-production.up.railway.app/api/v1'

# Get truck and driver
print('📍 Fetching trucks and drivers...')
trucks_r = requests.get(f'{BASE_URL}/trucks/?limit=1')
drivers_r = requests.get(f'{BASE_URL}/drivers/?limit=1')

truck = trucks_r.json()['results'][0]
driver = drivers_r.json()['results'][0]

print(f'✅ Truck: {truck["truck_identifier"]} ({truck["id"]})')
print(f'✅ Driver: {driver["first_name"]} {driver["last_name"]} ({driver["id"]})')

# Create mission
mission_data = {
    'identifier': 'MANICALAND-SCHOOL-001',
    'truck_id': truck['id'],
    'driver_id': driver['id'],
    'origin': {'lat': -18.975, 'lon': 32.655},
    'destination': {'lat': -18.985, 'lon': 32.65},
    'planned_distance_km': 12
}

print('\n📝 Creating mission...')
r = requests.post(f'{BASE_URL}/api-missions/create/', json=mission_data)

if r.status_code == 201:
    print(f'✅ Mission Created - Status: {r.status_code}')
    print(json.dumps(r.json(), indent=2))
else:
    print(f'❌ Status: {r.status_code}')
    print(json.dumps(r.json(), indent=2))

# Test location API
print('\n📍 Testing location API...')
loc_r = requests.get(f'{BASE_URL}/locations/autocomplete/?q=mutare')
print(f'✅ Location Search Status: {loc_r.status_code}')
locations = loc_r.json()['results']
print(f'Found {len(locations)} Manicaland locations:')
for loc in locations[:3]:
    print(f"  - {loc['name']} ({loc['type']}) @ {loc['lat']}, {loc['lon']}")
