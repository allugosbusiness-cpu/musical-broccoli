#!/usr/bin/env python
"""Monitor coordinate data flow from mobile app through backend to web app"""

import requests
import json
from datetime import datetime

def check_scanner_test_coordinates():
    """Check if SCANNER_TEST truck has correct coordinates"""
    print("\n" + "="*70)
    print("📊 COORDINATE MONITORING REPORT")
    print("="*70)
    
    # 1. Check backend truck data
    print("\n1️⃣  BACKEND TRUCK DATA (Local)")
    print("-" * 70)
    try:
        r = requests.get('http://localhost:8000/api/v1/trucks/?search=SCANNER_TEST')
        if r.status_code == 200:
            data = r.json()
            trucks = data.get('results', [])
            if trucks:
                truck = trucks[0]
                lat = truck.get('latitude')
                lon = truck.get('longitude')
                location = truck.get('location')
                
                print(f"✅ Truck Found: {truck.get('truck_identifier')}")
                print(f"   Plate: {truck.get('plate')}")
                print(f"   Latitude: {lat}")
                print(f"   Longitude: {lon}")
                print(f"   Location: {location}")
                print(f"   Current Location (JSON): {truck.get('current_location')}")
                
                # Compare with expected
                if lat and lon:
                    if float(lat) == -18.976323 and float(lon) == 32.683646:
                        print(f"\n   ✅ COORDINATES MATCH MOBILE APP! ✅")
                    else:
                        print(f"\n   ⚠️  Coordinates differ from mobile app")
                        print(f"      Expected: (-18.976323, 32.683646)")
                        print(f"      Got: ({lat}, {lon})")
                else:
                    print(f"\n   ❌ NO COORDINATES - Location not yet synced")
        else:
            print(f"❌ Error: {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 2. Check Render backend
    print("\n2️⃣  RENDER BACKEND DATA (Production)")
    print("-" * 70)
    try:
        r = requests.get('https://pulsetrack-back.onrender.com/api/v1/trucks/?search=SCANNER_TEST')
        if r.status_code == 200:
            data = r.json()
            trucks = data.get('results', [])
            if trucks:
                truck = trucks[0]
                lat = truck.get('latitude')
                lon = truck.get('longitude')
                location = truck.get('location')
                
                print(f"✅ Truck Found: {truck.get('truck_identifier')}")
                print(f"   Plate: {truck.get('plate')}")
                print(f"   Latitude: {lat}")
                print(f"   Longitude: {lon}")
                print(f"   Location: {location}")
                
                if lat and lon:
                    if float(lat) == -18.976323 and float(lon) == 32.683646:
                        print(f"\n   ✅ COORDINATES MATCH MOBILE APP! ✅")
                    else:
                        print(f"\n   ⚠️  Coordinates differ")
                else:
                    print(f"\n   ❌ NO COORDINATES")
        else:
            print(f"❌ Error: {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 3. Check location history
    print("\n3️⃣  LOCATION HISTORY (Last 5 locations)")
    print("-" * 70)
    try:
        # Get truck ID first
        r = requests.get('http://localhost:8000/api/v1/trucks/?search=SCANNER_TEST')
        if r.status_code == 200:
            trucks = r.json().get('results', [])
            if trucks:
                truck_id = trucks[0]['id']
                
                # Get truck locations
                r = requests.get(f'http://localhost:8000/api/v1/truck-locations/?truck={truck_id}&limit=5')
                if r.status_code == 200:
                    locations = r.json().get('results', [])
                    if locations:
                        print(f"✅ Found {len(locations)} location records:")
                        for i, loc in enumerate(locations[-5:], 1):
                            print(f"\n   [{i}] {loc.get('timestamp', 'N/A')}")
                            print(f"      Lat: {loc.get('latitude')}, Lon: {loc.get('longitude')}")
                            print(f"      Speed: {loc.get('speed')} km/h")
                    else:
                        print("❌ No location history found")
                else:
                    print(f"⚠️  Status {r.status_code}")
    except Exception as e:
        print(f"⚠️  Error: {e}")
    
    print("\n" + "="*70)
    print("📝 SUMMARY")
    print("="*70)
    print("""
✅ What We Fixed:
   - Backend now updates truck coordinates when mobile sends location
   - Two endpoints fixed: start_mission_tracking & mobile_location_update
   - Coordinates saved to both TruckLocation (history) and FleetTruck (display)

🔄 How It Works Now:
   1. Mobile app gets location: -18.976323, 32.683646
   2. Sends to backend via /mobile/location-update/ or mission start
   3. Backend SAVES to FleetTruck.latitude & .longitude
   4. Web app fetches truck data and shows correct coordinates
   5. Truck icon appears on Global Map with correct position

📍 Next Steps:
   1. Ensure mobile app is sending locations (check Metro logs)
   2. Reload web app dashboard
   3. Verify truck shows correct location on map
   4. Check that trails display correctly
""")

if __name__ == "__main__":
    check_scanner_test_coordinates()
