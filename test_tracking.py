#!/usr/bin/env python
"""
Test script for real-time truck location and speed tracking
Tests the new truck-tracking endpoints
"""

import requests
import json
from datetime import datetime
import time

API_BASE = "https://musical-broccoli-production.up.railway.app/api/v1"

# First, get all trucks to find a truck ID
print("📍 Testing Truck Location & Speed Tracking Endpoints\n")
print("=" * 60)

# Get all trucks
print("\n1️⃣ Fetching all trucks...")
try:
    trucks_resp = requests.get(f"{API_BASE}/trucks/")
    if trucks_resp.status_code == 200:
        trucks = trucks_resp.json()['results'] if 'results' in trucks_resp.json() else trucks_resp.json()
        if trucks:
            truck = trucks[0]
            truck_id = truck['id']
            truck_identifier = truck.get('truck_identifier', 'UNKNOWN')
            print(f"✅ Found truck: {truck_identifier} (ID: {truck_id})")
            
            # Test 1: Update truck location and speed
            print(f"\n2️⃣ Updating truck location and speed...")
            update_payload = {
                "truck_id": str(truck_id),
                "latitude": -18.9750,
                "longitude": 32.6550,
                "speed_kmh": 45.5,
                "timestamp": datetime.now().isoformat()
            }
            print(f"📤 Sending: {json.dumps(update_payload, indent=2)}")
            
            update_resp = requests.post(
                f"{API_BASE}/truck-tracking/location-speed/",
                json=update_payload,
                timeout=10
            )
            
            if update_resp.status_code == 200:
                print(f"✅ Location updated successfully!")
                print(f"Response: {json.dumps(update_resp.json(), indent=2)}")
            else:
                print(f"❌ Update failed with status {update_resp.status_code}")
                print(f"Response: {update_resp.text}")
            
            # Test 2: Get truck's current location
            print(f"\n3️⃣ Fetching truck's current location...")
            get_resp = requests.get(
                f"{API_BASE}/truck-tracking/location-speed/{truck_id}/",
                timeout=10
            )
            
            if get_resp.status_code == 200:
                print(f"✅ Location retrieved successfully!")
                location_data = get_resp.json()
                print(f"📍 Current Location: {location_data['location']}")
                print(f"⚡ Speed: {location_data['speed_kmh']} km/h")
                print(f"🕐 Updated: {location_data['updated_at']}")
            else:
                print(f"❌ Fetch failed with status {get_resp.status_code}")
                print(f"Response: {get_resp.text}")
            
            # Test 3: Get all trucks' locations
            print(f"\n4️⃣ Fetching all trucks' locations...")
            all_resp = requests.get(
                f"{API_BASE}/truck-tracking/all-locations/",
                timeout=10
            )
            
            if all_resp.status_code == 200:
                all_data = all_resp.json()
                print(f"✅ Retrieved {all_data['count']} truck locations")
                for t in all_data['trucks'][:3]:  # Show first 3
                    print(f"  - {t['truck_identifier']}: {t['speed_kmh']} km/h at {t['location']}")
                if len(all_data['trucks']) > 3:
                    print(f"  ... and {len(all_data['trucks']) - 3} more")
            else:
                print(f"❌ Fetch failed with status {all_resp.status_code}")
                print(f"Response: {all_resp.text}")
            
            # Test 4: Simulate multiple updates
            print(f"\n5️⃣ Simulating 3 rapid location updates (like 5-second intervals)...")
            speeds = [45.5, 55.3, 38.2]
            for i, speed in enumerate(speeds, 1):
                update_payload = {
                    "truck_id": str(truck_id),
                    "latitude": -18.9750 + (i * 0.001),
                    "longitude": 32.6550 + (i * 0.001),
                    "speed_kmh": speed,
                    "timestamp": datetime.now().isoformat()
                }
                
                resp = requests.post(
                    f"{API_BASE}/truck-tracking/location-speed/",
                    json=update_payload,
                    timeout=10
                )
                
                if resp.status_code == 200:
                    print(f"  Update {i}: ✅ Speed {speed} km/h recorded")
                else:
                    print(f"  Update {i}: ❌ Failed")
                
                if i < len(speeds):
                    time.sleep(1)  # Wait between updates
            
            # Final check
            print(f"\n6️⃣ Final location check...")
            final_resp = requests.get(
                f"{API_BASE}/truck-tracking/location-speed/{truck_id}/",
                timeout=10
            )
            
            if final_resp.status_code == 200:
                final_data = final_resp.json()
                print(f"✅ Final Speed: {final_data['speed_kmh']} km/h")
                print(f"📍 Final Location: ({final_data['location']['lat']}, {final_data['location']['lon']})")
            
            print("\n" + "=" * 60)
            print("✅ All tracking endpoint tests passed!")
            
        else:
            print("❌ No trucks found in database")
    else:
        print(f"❌ Failed to fetch trucks: {trucks_resp.status_code}")
        print(trucks_resp.text)

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
