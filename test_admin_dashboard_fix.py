#!/usr/bin/env python
"""
Test admin dashboard mission creation (after field name fixes)
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
print("TEST: Admin Dashboard Mission Creation (After Fixes)")
print("=" * 70)

client = Client()

# Get test data
trucks = list(FleetTruck.objects.all())[:1]
drivers = list(FleetDriver.objects.all())[:1]

if trucks and drivers:
    truck = trucks[0]
    driver = drivers[0]
    
    print(f"\n1. Admin Dashboard form submits with:")
    print(f"   truck_id: {truck.id}")
    print(f"   driver_id: {driver.id}")
    
    # This simulates what the admin dashboard form sends (with fixed field names)
    payload = {
        "mission_number": f"ADMIN-DASH-TEST-{uuid.uuid4().hex[:8]}",
        "truck": truck.id,  # FIXED: now using 'truck' instead of 'truck_id'
        "driver": driver.id,  # FIXED: now using 'driver' instead of 'driver_id'
        "status": "planned",
        "origin": {
            "name": "Admin Test Origin",
            "lat": -1.2921,
            "lng": 36.8219,
        },
        "destination": {
            "name": "Admin Test Destination",
            "lat": -1.2850,
            "lng": 36.8270,
        },
        "priority": "normal",
        "distance_total_m": 0,  # Will be auto-calculated
        "progress_pct": 0,
    }
    
    response = client.post(
        '/api/v1/missions/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    print(f"\n2. API Response: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = json.loads(response.content)
        mission_id = result.get('id')
        
        print(f"\n3. Mission Created Successfully:")
        print(f"   Mission #: {result.get('mission_number')}")
        print(f"   truck_name: {result.get('truck_name')}")
        print(f"   driver_name: {result.get('driver_name')}")
        print(f"   distance_total_m: {result.get('distance_total_m')}")
        print(f"   status: {result.get('status')}")
        
        # Verify via dashboard endpoint
        print(f"\n4. Verify via dashboard endpoint:")
        dashboard_response = client.get('/api/v1/dashboard/missions/')
        dashboard_missions = json.loads(dashboard_response.content)
        
        # Find our mission
        our_mission = next((m for m in dashboard_missions if m.get('id') == mission_id), None)
        
        if our_mission:
            print(f"   ✓ Found in dashboard")
            print(f"   truck_name: {our_mission.get('truck_name')}")
            print(f"   driver_name: {our_mission.get('driver_name')}")
            print(f"   distance_total_m: {our_mission.get('distance_total_m')}")
            
            # Check if display would work correctly
            truck_display = our_mission.get('truck_name') or 'Unassigned'
            driver_display = our_mission.get('driver_name') or 'Unassigned'
            distance_km = (float(our_mission.get('distance_total_m', 0)) / 1000) if our_mission.get('distance_total_m') else 'N/A'
            
            print(f"\n5. How it would display in admin dashboard:")
            print(f"   Truck: {truck_display}")
            print(f"   Driver: {driver_display}")
            print(f"   Distance: {distance_km if distance_km == 'N/A' else f'{distance_km:.1f}km'}")
            
            if truck_display != 'Unassigned' and driver_display != 'Unassigned' and distance_km != 'N/A':
                print(f"\n✅ SUCCESS: All fields display correctly!")
            else:
                print(f"\n❌ ISSUE: Some fields would display as default!")
        else:
            print(f"   ✗ Mission not found in dashboard!")
    else:
        print(f"Error: {response.content.decode('utf-8', errors='ignore')}")
else:
    print("No test data available!")

print("\n" + "=" * 70)
