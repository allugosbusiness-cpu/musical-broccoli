#!/usr/bin/env python
"""
Final verification script - Tests all fixes are working in production
Run this after Render deployment completes
"""

import urllib.request
import json
import time
import sys

print("="*70)
print("🔍 FINAL VERIFICATION - PULSETRACK FIXES")
print("="*70)

# Give deployment time to settle if needed
deployment_wait = 10
print(f"\n⏳ Waiting {deployment_wait} seconds for deployment to settle...")
time.sleep(deployment_wait)

test_passed = 0
test_failed = 0

def test_endpoint(name, url, method="GET", data=None, expected_fields=None):
    """Test an endpoint and verify response"""
    global test_passed, test_failed
    
    print(f"\n{'='*70}")
    print(f"🧪 TEST: {name}")
    print(f"{'='*70}")
    print(f"   URL: {url}")
    print(f"   Method: {method}")
    
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        
        if data:
            response = urllib.request.urlopen(req, data=json.dumps(data).encode("utf-8"), timeout=15)
        else:
            response = urllib.request.urlopen(req, timeout=15)
        
        result = json.loads(response.read().decode("utf-8"))
        
        print(f"   ✅ Status: HTTP {response.status}")
        
        # Check expected fields
        if expected_fields:
            missing = []
            for field in expected_fields:
                if field not in result and (not isinstance(result, list) or (isinstance(result, list) and len(result) > 0 and field not in result[0])):
                    missing.append(field)
            
            if missing:
                print(f"   ⚠️  Missing fields: {missing}")
                test_failed += 1
                return False
            else:
                print(f"   ✅ All expected fields present")
                test_passed += 1
                return True
        else:
            print(f"   ✅ Response received")
            test_passed += 1
            return True
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        test_failed += 1
        return False

# ============================================================
# TEST 1: Mission creation with coordinates
# ============================================================
mission_data = {
    "mission_number": f"VERIFY-{int(time.time())}",
    "status": "planned",
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

test_endpoint(
    "Create Mission with Distance Calculation",
    "https://pulsetrack-back.onrender.com/api/v1/missions/",
    method="POST",
    data=mission_data,
    expected_fields=['id', 'truck_name', 'driver_name', 'distance_total_m']
)

# ============================================================
# TEST 2: Fetch missions and verify display fields
# ============================================================
test_endpoint(
    "Fetch Dashboard Missions (display fields)",
    "https://pulsetrack-back.onrender.com/api/v1/dashboard/missions/",
    method="GET",
    expected_fields=['truck_name', 'driver_name', 'distance_total_m']
)

# ============================================================
# TEST 3: Calculate distance endpoint
# ============================================================
distance_test_data = {
    "origin": {"lat": -17.8252, "lon": 31.0335},
    "destination": {"lat": -20.1551, "lon": 28.5679}
}

test_endpoint(
    "Calculate Distance Endpoint",
    "https://pulsetrack-back.onrender.com/api/v1/calculate-distance/",
    method="POST",
    data=distance_test_data,
    expected_fields=['distance_m', 'distance_meters']
)

# ============================================================
# TEST 4: Mobile driver available missions
# ============================================================
test_endpoint(
    "Mobile: Get Available Missions",
    "https://pulsetrack-back.onrender.com/api/v1/mobile/driver/c1c0e021-6f48-42fd-a733-b928784c51bb/available-missions/",
    method="GET",
    expected_fields=['missions', 'driver_name', 'truck_name']
)

# ============================================================
# SUMMARY
# ============================================================
print(f"\n\n{'='*70}")
print("📊 VERIFICATION SUMMARY")
print(f"{'='*70}")
print(f"✅ Passed: {test_passed}")
print(f"❌ Failed: {test_failed}")
print(f"{'='*70}")

if test_failed == 0:
    print("\n🎉 ALL TESTS PASSED! Fixes are working correctly.")
    sys.exit(0)
else:
    print(f"\n⚠️  {test_failed} test(s) failed. Review output above.")
    sys.exit(1)
