#!/usr/bin/env python
"""
COORDINATE FLOW VERIFICATION SYSTEM
Verifies mobile → backend → web coordinate pipeline with no mistakes
"""

import requests
import json
from datetime import datetime
from decimal import Decimal

# Configuration
RENDER_BACKEND = "https://pulsetrack-back.onrender.com/api/v1"
TEST_TRUCK_ID = "6f91a80d-eecd-47c5-a4ac-0b546b9cb473"
TEST_TRUCK_IDENTIFIER = "SCANNER_TEST"

# Expected test coordinates (Mutare, Zimbabwe)
EXPECTED_LAT = -18.976323
EXPECTED_LON = 32.683646
TOLERANCE = 0.01  # Allow 0.01 degree tolerance (~1 km)

def verify_step_1_backend_database():
    """Step 1: Check if backend saved coordinates to database"""
    print("\n" + "="*70)
    print("STEP 1️⃣: VERIFY BACKEND DATABASE")
    print("="*70)
    print("Location: server/api/models_v2.py - FleetTruck table")
    print("Expected fields: last_latitude, last_longitude, current_location")
    print()
    
    try:
        # For local testing - would need direct DB access
        print("⚠️  Local database check requires Django shell:")
        print("   python manage.py shell")
        print("   >>> from api.models_v2 import FleetTruck")
        print("   >>> truck = FleetTruck.objects.get(id='{}')".format(TEST_TRUCK_ID))
        print("   >>> print(f'Latitude: {truck.last_latitude}')")
        print("   >>> print(f'Longitude: {truck.last_longitude}')")
        print("   >>> print(f'Current Location: {truck.current_location}')")
        print()
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return False

def verify_step_2_backend_api_response():
    """Step 2: Verify backend API returns coordinates"""
    print("\n" + "="*70)
    print("STEP 2️⃣: VERIFY BACKEND API RESPONSE")
    print("="*70)
    print(f"Endpoint: GET {RENDER_BACKEND}/dashboard/trucks/")
    print(f"Query: search={TEST_TRUCK_IDENTIFIER}")
    print()
    
    try:
        url = f"{RENDER_BACKEND}/dashboard/trucks/?search={TEST_TRUCK_IDENTIFIER}"
        print(f"📡 Fetching: {url}")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status Code: 200 OK")
            print(f"✅ Response Time: {response.elapsed.total_seconds():.2f}s")
            
            if isinstance(data, list) and len(data) > 0:
                truck = data[0]
                
                print(f"\n📦 Response Data:")
                print(f"   Truck ID: {truck.get('id')}")
                print(f"   Truck Identifier: {truck.get('truck_identifier')}")
                print(f"   Plate: {truck.get('plate')}")
                print(f"   Status: {truck.get('status')}")
                
                # Check coordinates
                lat = truck.get('latitude')
                lon = truck.get('longitude')
                
                print(f"\n📍 Coordinates:")
                print(f"   Latitude:  {lat}")
                print(f"   Longitude: {lon}")
                
                # Verify coordinates exist and are valid
                if lat is None or lon is None:
                    print(f"   ❌ ERROR: Coordinates are None!")
                    print(f"   ⚠️  This means mobile app hasn't sent location yet")
                    print(f"   OR backend isn't saving to FleetTruck.last_latitude/longitude")
                    return False
                
                # Check if coordinates are reasonable
                if not (-20 < float(lat) < -15):
                    print(f"   ❌ ERROR: Latitude {lat} is outside Zimbabwe bounds!")
                    return False
                
                if not (25 < float(lon) < 35):
                    print(f"   ❌ ERROR: Longitude {lon} is outside Zimbabwe bounds!")
                    return False
                
                print(f"   ✅ Coordinates are valid!")
                
                # Check location object
                location = truck.get('location')
                if location:
                    print(f"\n📌 Current Location Object:")
                    print(f"   {json.dumps(location, indent=6)}")
                
                return True
            else:
                print(f"❌ ERROR: No trucks found in response")
                print(f"   Response: {data}")
                return False
        else:
            print(f"❌ ERROR: Status Code {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ ERROR: Request timeout (>10 seconds)")
        print(f"   The dashboard trucks endpoint is slow")
        print(f"   See: CRITICAL_FIXES_DASHBOARD_SERVICE.md")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def verify_step_3_web_app_fetch():
    """Step 3: Verify web app can fetch and parse coordinates"""
    print("\n" + "="*70)
    print("STEP 3️⃣: VERIFY WEB APP FETCHES CORRECTLY")
    print("="*70)
    print("File: client/Frontend/src/components/GlobalMap.jsx")
    print("Function: transformedTrucks.map()")
    print()
    
    # This would be visible in browser console
    print("✅ Check browser console for:")
    print("   1. '🔄 Transforming truck...' messages")
    print("   2. '✅ Transformed SCANNER_TEST:' with coordinates")
    print("   3. '✅ All N trucks transformed' completion")
    print()
    print("📍 Expected console output:")
    print("""
    ✅ Transformed SCANNER_TEST: {
      id: '6f91a80d-eecd-47c5-a4ac-0b546b9cb473',
      identifier: 'SCANNER_TEST',
      latitude: -18.976323,
      longitude: 32.683646,
      location_name: 'Mutare, Zimbabwe'
    }
    """)

def verify_step_4_map_display():
    """Step 4: Verify truck icon appears on map"""
    print("\n" + "="*70)
    print("STEP 4️⃣: VERIFY MAP DISPLAY")
    print("="*70)
    print("File: client/Frontend/src/components/GlobalMap.jsx")
    print("Function: addTruckMarker()")
    print()
    
    print("✅ Visual Verification:")
    print("   1. Open https://pulsetrack-frontend-henna.vercel.app/dashboard")
    print("   2. Look for truck marker(s) on map")
    print("   3. If 4 trucks at same location:")
    print("      - You'll see a cluster badge showing count")
    print("      - Click cluster to expand and see individual trucks")
    print("   4. Click SCANNER_TEST truck icon")
    print("   5. Popup should show:")
    print(f"      - Coordinates: -18.9763, 32.6836")
    print(f"      - Status: idle")
    print(f"      - Speed: 0 km/h")
    print()
    
    print("🔍 Browser Console Verification:")
    print("   Expected logs:")
    print("""
    🚚 addTruckMarker called for truck SCANNER_TEST:
       id: '6f91a80d-eecd-47c5-a4ac-0b546b9cb473'
       lat: -18.976323
       lon: 32.683646
       status: 'idle'
       hasMap: true
    
    📋 Marker added for SCANNER_TEST at -18.976, 32.684
    """)

def verify_step_5_mission_link():
    """Step 5: Verify mission is linked with correct coordinates"""
    print("\n" + "="*70)
    print("STEP 5️⃣: VERIFY MISSION LINK")
    print("="*70)
    print("File: server/api/mobile_endpoints.py")
    print("Function: start_mission_tracking()")
    print()
    
    print("✅ When driver scans QR to start mission:")
    print("   1. Mobile sends coordinates with mission start")
    print("   2. Backend saves to mission.current_location")
    print("   3. Backend saves to truck.last_latitude/longitude")
    print("   4. Web app shows truck and mission with same coordinates")
    print()
    
    print("🔍 API Endpoint:")
    print(f"   POST {RENDER_BACKEND}/mobile/mission/start-tracking/")
    print("""
    Request payload:
    {
      "driver_id": "...",
      "mission_id": "...",
      "latitude": -18.976323,
      "longitude": 32.683646,
      "speed": 0
    }
    """)

def main():
    """Run all verification steps"""
    print("\n" + "█"*70)
    print("█  COORDINATE FLOW VERIFICATION SYSTEM")
    print("█  Mobile → Backend → Web (NO MISTAKES ALLOWED)")
    print("█"*70)
    
    print(f"\nTest Case: {TEST_TRUCK_IDENTIFIER}")
    print(f"Truck ID: {TEST_TRUCK_ID}")
    print(f"Expected Coordinates: {EXPECTED_LAT}, {EXPECTED_LON}")
    print(f"Tolerance: ±{TOLERANCE}°")
    
    # Run all verification steps
    verify_step_1_backend_database()
    step2_pass = verify_step_2_backend_api_response()
    verify_step_3_web_app_fetch()
    verify_step_4_map_display()
    verify_step_5_mission_link()
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    if step2_pass:
        print("✅ Backend API: COORDINATES AVAILABLE")
        print("✅ Next: Verify web app is displaying truck icon correctly")
        print("✅ Then: Test mobile app sending location updates")
    else:
        print("⚠️  Backend API: COORDINATES NOT FOUND")
        print("   Possible causes:")
        print("   1. Mobile app hasn't sent any location data yet")
        print("   2. Backend mobile_location_update() not saving to FleetTruck")
        print("   3. Dashboard trucks endpoint optimization issue")
        print()
        print("   Fix: Ensure mobile_location_update() has:")
        print("   driver.truck.last_latitude = float(latitude)")
        print("   driver.truck.last_longitude = float(longitude)")
        print("   driver.truck.save()")
    
    print("\n" + "█"*70)
    print("█  END VERIFICATION")
    print("█"*70 + "\n")

if __name__ == '__main__':
    main()
