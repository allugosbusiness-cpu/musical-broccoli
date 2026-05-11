#!/usr/bin/env python3
"""
Test activity endpoints
"""
import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:8000'

print("=" * 60)
print("🧪 TESTING ACTIVITY ENDPOINTS")
print("=" * 60)

# Test 1: Log an activity
print("\n✏️ TEST 1: Log Activity")
print("-" * 60)
activity_data = {
    'activity_type': 'trail_recorded',
    'activity_category': 'trail',
    'location_lat': -18.975,
    'location_lon': 32.655,
    'location_name': 'Mutare CBD',
    'speed_kmh': 45.5,
    'distance_m': 1234.5,
    'is_critical': False,
    'notes': 'Test activity from endpoint testing'
}

try:
    resp = requests.post(f'{BASE_URL}/api/v1/activities/log/', json=activity_data)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 201:
        data = resp.json()
        print(f"✅ Activity logged successfully!")
        print(f"   Activity ID: {data.get('activity_id')}")
        print(f"   Type: {data.get('activity_type')}")
        print(f"   Timestamp: {data.get('timestamp')}")
    else:
        print(f"❌ Error: {resp.text}")
except Exception as e:
    print(f"❌ Connection error: {e}")

# Test 2: Get activities
print("\n📊 TEST 2: Get Activities")
print("-" * 60)
try:
    resp = requests.get(f'{BASE_URL}/api/v1/activities/', params={'days': 7, 'limit': 10})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Activities retrieved successfully!")
        print(f"   Total activities: {data.get('total_count')}")
        print(f"   Returned: {data.get('count')} records")
        if data.get('activities'):
            print(f"   Sample activity: {data['activities'][0].get('activity_type_display')}")
    else:
        print(f"❌ Error: {resp.text}")
except Exception as e:
    print(f"❌ Connection error: {e}")

# Test 3: Get activity summary
print("\n📈 TEST 3: Activity Summary")
print("-" * 60)
try:
    resp = requests.get(f'{BASE_URL}/api/v1/activities/summary/', params={'days': 7})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Summary retrieved successfully!")
        print(f"   Total activities: {data.get('total_activities')}")
        print(f"   Critical events: {data.get('critical_count')}")
        print(f"   Categories: {list(data.get('by_category', {}).keys())}")
    else:
        print(f"❌ Error: {resp.text}")
except Exception as e:
    print(f"❌ Connection error: {e}")

# Test 4: Get critical activities
print("\n🚨 TEST 4: Critical Activities")
print("-" * 60)
try:
    resp = requests.get(f'{BASE_URL}/api/v1/activities/critical/', params={'days': 7, 'limit': 10})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Critical activities retrieved successfully!")
        print(f"   Total critical: {data.get('count')}")
    else:
        print(f"❌ Error: {resp.text}")
except Exception as e:
    print(f"❌ Connection error: {e}")

print("\n" + "=" * 60)
print("✅ ACTIVITY ENDPOINT TESTING COMPLETE")
print("=" * 60)
