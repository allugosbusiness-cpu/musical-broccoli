#!/usr/bin/env python
"""
Advanced diagnostic script to debug serializer behavior and API responses
"""

import urllib.request
import json
import time

print("="*70)
print("ADVANCED DIAGNOSTICS: SERIALIZER & DISTANCE CALCULATION")
print("="*70)

# Test 1: Verify serializer is calling _calculate_distance
print("\n1️⃣  DIRECT SERIALIZER TEST (Python)")
print("-" * 70)

try:
    import os
    import sys
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
    sys.path.insert(0, 'server')
    django.setup()
    
    from server.api.serializers import MissionSerializer
    from decimal import Decimal
    
    # Test data with coordinates
    test_data = {
        "mission_number": "SERIALIZER-TEST-001",
        "status": "planned",
        "truck": "d16aaa81-1bba-4a20-b76f-ab8d23ed71f3",
        "driver": "c1c0e021-6f48-42fd-a733-b928784c51bb",
        "origin": {
            "name": "Harare",
            "lat": -17.8252,
            "lon": 31.0335
        },
        "destination": {
            "name": "Bulawayo",
            "lat": -20.1551,
            "lon": 28.5679
        }
    }
    
    print("📝 Test Data:")
    print(f"   Origin: {test_data['origin']}")
    print(f"   Destination: {test_data['destination']}")
    
    # Create serializer instance
    serializer = MissionSerializer(data=test_data)
    
    if serializer.is_valid():
        print("\n✅ Serializer validation passed")
        print(f"   Validated data keys: {list(serializer.validated_data.keys())}")
        
        # Check if distance was calculated
        if 'distance_total_m' in serializer.validated_data:
            distance = serializer.validated_data['distance_total_m']
            print(f"\n   distance_total_m: {distance}")
            if distance == 0 or distance is None:
                print(f"   ⚠️  Distance is 0 or None - serializer create() may not have been called")
            else:
                print(f"   ✅ Distance calculated: {float(distance):.2f} meters")
        else:
            print(f"   ⚠️  distance_total_m not in validated data")
        
        # Now try to create to trigger the create() method
        print("\n📍 Calling serializer.create()...")
        instance = serializer.save()
        print(f"   ✅ Mission created: {instance.id}")
        print(f"   After create: distance_total_m = {instance.distance_total_m}")
        
        if float(instance.distance_total_m) == 0:
            print(f"   ⚠️  Distance still 0 after creation - _calculate_distance not working")
        else:
            print(f"   ✅ Distance properly calculated: {float(instance.distance_total_m)} meters")
        
    else:
        print(f"❌ Serializer validation failed:")
        print(json.dumps(serializer.errors, indent=2))
        
except Exception as e:
    print(f"❌ Error in serializer test: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 2: Check what the API endpoint actually returns
print("\n\n2️⃣  API ENDPOINT TEST (HTTP POST)")
print("-" * 70)

mission_data = {
    "mission_number": f"API-TEST-{int(time.time())}",
    "status": "planned",
    "truck": "d16aaa81-1bba-4a20-b76f-ab8d23ed71f3",
    "driver": "c1c0e021-6f48-42fd-a733-b928784c51bb",
    "origin": {
        "name": "Harare",
        "lat": -17.8252,
        "lon": 31.0335
    },
    "destination": {
        "name": "Bulawayo",
        "lat": -20.1551,
        "lon": 28.5679
    }
}

print(f"📤 Posting mission data:")
print(json.dumps(mission_data, indent=2))

try:
    req = urllib.request.Request(
        "https://pulsetrack-back.onrender.com/api/v1/missions/",
        method="POST"
    )
    req.add_header("Content-Type", "application/json")
    
    response = urllib.request.urlopen(
        req,
        data=json.dumps(mission_data).encode("utf-8"),
        timeout=15
    )
    result = json.loads(response.read().decode("utf-8"))
    
    print(f"\n📥 API Response:")
    print(json.dumps(result, indent=2))
    
    print(f"\n🔍 Key Fields:")
    print(f"   truck: {result.get('truck')}")
    print(f"   truck_name: {result.get('truck_name')}")
    print(f"   driver: {result.get('driver')}")
    print(f"   driver_name: {result.get('driver_name')}")
    print(f"   distance_total_m: {result.get('distance_total_m')}")
    
    # Now fetch the mission to see what gets returned
    mission_id = result.get('id')
    if mission_id:
        print(f"\n\n3️⃣  FETCH MISSION TEST (HTTP GET)")
        print("-" * 70)
        print(f"📍 Fetching mission {mission_id}...")
        
        req = urllib.request.Request(
            f"https://pulsetrack-back.onrender.com/api/v1/missions/{mission_id}/",
            method="GET"
        )
        response = urllib.request.urlopen(req, timeout=10)
        result = json.loads(response.read().decode("utf-8"))
        
        print(f"\n📥 Fetched Mission:")
        print(json.dumps(result, indent=2))
        
        print(f"\n🔍 Key Fields on Fetch:")
        print(f"   truck: {result.get('truck')}")
        print(f"   truck_name: {result.get('truck_name')}")
        print(f"   driver: {result.get('driver')}")
        print(f"   driver_name: {result.get('driver_name')}")
        print(f"   distance_total_m: {result.get('distance_total_m')}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
