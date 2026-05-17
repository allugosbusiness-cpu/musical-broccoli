#!/usr/bin/env python
"""Check coordinate mismatch for SCANNER_TEST truck"""

import requests
import json

# Get SCANNER_TEST truck data
r = requests.get('https://pulsetrack-back.onrender.com/api/v1/trucks/?search=SCANNER_TEST')
if r.status_code == 200:
    data = r.json()
    trucks = data.get('results', [])
    if trucks:
        truck = trucks[0]
        print('\n📍 SCANNER_TEST Truck Data from Backend:')
        print(f'  ID: {truck.get("id")}')
        print(f'  Truck Identifier: {truck.get("truck_identifier")}')
        print(f'  Plate: {truck.get("plate")}')
        print(f'  Latitude: {truck.get("latitude")}')
        print(f'  Longitude: {truck.get("longitude")}')
        print(f'  Location: {truck.get("location")}')
        print()
        print('📱 Expected from Mobile App:')
        print('  Latitude: -18.976323')
        print('  Longitude: 32.683646')
        print()
        
        # Check if coordinates match
        lat = float(truck.get("latitude") or 0)
        lon = float(truck.get("longitude") or 0)
        
        if lat == -18.976323 and lon == 32.683646:
            print('✅ Coordinates MATCH!')
        elif lat == 32.683646 and lon == -18.976323:
            print('❌ ISSUE FOUND: Coordinates are REVERSED (lat/lon swapped)')
        else:
            print(f'❌ COORDINATES MISMATCH: Backend has ({lat}, {lon})')
            print(f'   Expected: (-18.976323, 32.683646)')
else:
    print(f'Error fetching truck data: {r.status_code}')
