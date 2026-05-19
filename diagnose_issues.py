#!/usr/bin/env python
"""
Diagnostic script to identify and test issues with:
1. Mobile app endpoints
2. Mission creation with truck/driver assignment
3. Distance calculation
"""

import urllib.request
import json
import time

print("="*60)
print("PULSETRACK DIAGNOSTIC SCRIPT")
print("="*60)

# ============================================================
# 1. MOBILE APP CONFIGURATION
# ============================================================
print("\n1️⃣  MOBILE APP DATA ENDPOINTS")
print("-" * 60)

mobile_config = {
    "api_base_url": "https://pulsetrack-back.onrender.com/api/v1",
    "endpoints": {
        "available_missions": "/mobile/driver/{driver_id}/available-missions/",
        "mission_start_tracking": "/mobile/mission/start-tracking/",
        "location_updates": "/truck-tracking/location-speed/",
        "driver_registration": "/mobile/driver/registration/"
    }
}

print("✅ Mobile App Configuration:")
print(f"   Backend: {mobile_config['api_base_url']}")
print(f"   Key Endpoints:")
for name, endpoint in mobile_config['endpoints'].items():
    full_url = mobile_config['api_base_url'] + endpoint
    print(f"   - {name}: {full_url}")

# ============================================================
# 2. TEST MISSION CREATION WITH TRUCK/DRIVER
# ============================================================
print("\n\n2️⃣  MISSION CREATION TEST (with truck/driver)")
print("-" * 60)

mission_data = {
    "mission_number": f"DIAG-{int(time.time())}",
    "status": "planned",
    "priority": "high",
    "truck": "d16aaa81-1bba-4a20-b76f-ab8d23ed71f3",
    "driver": "c1c0e021-6f48-42fd-a733-b928784c51bb",
    "origin": {
        "name": "Harare Central",
        "lat": -17.8252,
        "lon": 31.0335
    },
    "destination": {
        "name": "Bulawayo Main",
        "lat": -20.1551,
        "lon": 28.5679
    }
}

print(f"📤 Sending mission:")
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
        timeout=10
    )
    result = json.loads(response.read().decode("utf-8"))
    
    print(f"\n✅ HTTP {response.status}")
    print(f"📥 Response from API:")
    print(json.dumps(result, indent=2))
    
    # Check for the key fields
    print(f"\n🔍 Field Check:")
    print(f"   ✓ truck: {result.get('truck')} (ID)")
    print(f"   ✓ truck_name: {result.get('truck_name')} (Display Name)")
    print(f"   ✓ driver: {result.get('driver')} (ID)")
    print(f"   ✓ driver_name: {result.get('driver_name')} (Display Name)")
    print(f"   ✓ distance_total_m: {result.get('distance_total_m')} meters")
    
    # Calculate expected distance
    from math import radians, cos, sin, asin, sqrt
    lon1, lat1 = mission_data['origin']['lon'], mission_data['origin']['lat']
    lon2, lat2 = mission_data['destination']['lon'], mission_data['destination']['lat']
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    expected_km = 6371 * c
    print(f"\n   📏 Expected distance (Haversine): {expected_km:.1f} km = {int(expected_km * 1000)} meters")
    if result.get('distance_total_m'):
        actual_km = float(result.get('distance_total_m')) / 1000
        print(f"   📏 Actual distance: {actual_km:.1f} km")
        diff = abs(expected_km - actual_km)
        if diff < 5:
            print(f"   ✅ Distance matches! (diff: {diff:.1f} km)")
        else:
            print(f"   ⚠️  Distance mismatch (diff: {diff:.1f} km)")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print(f"   This may indicate the API is not available or there's a validation error")

# ============================================================
# 3. TEST FETCHING MISSIONS TO SEE WHAT'S DISPLAYED
# ============================================================
print("\n\n3️⃣  FETCH MISSIONS TEST (what dashboard displays)")
print("-" * 60)

try:
    req = urllib.request.Request(
        "https://pulsetrack-back.onrender.com/api/v1/dashboard/missions/",
        method="GET"
    )
    response = urllib.request.urlopen(req, timeout=10)
    missions = json.loads(response.read().decode("utf-8"))
    
    if isinstance(missions, list) and len(missions) > 0:
        print(f"✅ Found {len(missions)} missions")
        print(f"\n📋 Sample Mission (most recent):")
        sample = missions[0]
        print(f"   Mission #: {sample.get('mission_number')}")
        print(f"   Truck: {sample.get('truck')} (ID)")
        print(f"   Truck Name: {sample.get('truck_name')} (Display)")
        print(f"   Driver: {sample.get('driver')} (ID)")
        print(f"   Driver Name: {sample.get('driver_name')} (Display)")
        print(f"   Status: {sample.get('status')}")
        print(f"   Distance: {sample.get('distance_total_m')} meters")
        
        # Check if the issue exists
        print(f"\n🔍 Issue Check:")
        if not sample.get('truck_name'):
            print(f"   ❌ truck_name is missing or null - this causes 'Unassigned' display!")
        else:
            print(f"   ✅ truck_name is set")
            
        if not sample.get('driver_name'):
            print(f"   ❌ driver_name is missing or null - this causes 'Unassigned' display!")
        else:
            print(f"   ✅ driver_name is set")
            
        if not sample.get('distance_total_m'):
            print(f"   ❌ distance_total_m is missing or 0 - distance not calculated!")
        else:
            print(f"   ✅ distance_total_m is set")
    else:
        print(f"✅ No missions found (empty list)")
        
except Exception as e:
    print(f"❌ Error fetching missions: {str(e)}")

# ============================================================
# 4. SUMMARY AND RECOMMENDATIONS
# ============================================================
print("\n\n4️⃣  SUMMARY & RECOMMENDATIONS")
print("-" * 60)
print("""
Mobile App Data Flow:
  📱 Mobile App (Expo) → https://pulsetrack-back.onrender.com/api/v1
  - Driver login with registration
  - Gets available missions for driver
  - Updates mission tracking/delivery status
  - Sends GPS coordinates for location tracking

Dashboard Issues to Fix:
  ✓ If truck_name/driver_name show 'Unassigned':
    → Check if serializer is returning these fields
    → Verify truck/driver relationships are saved
    → May need to refresh data after creation
    
  ✓ If distance shows 0 or isn't calculated:
    → Check if origin/destination coordinates are valid
    → Verify serializer's _calculate_distance method
    → May need to use OSRM API instead of Haversine
""")

print("\n" + "="*60)
print("✅ DIAGNOSTIC COMPLETE")
print("="*60)
