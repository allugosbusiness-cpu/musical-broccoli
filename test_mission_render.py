#!/usr/bin/env python
"""
Test mission creation on production Render backend
Run this after Render deployment completes
"""
import requests
import json
import time
from datetime import datetime

BACKEND_URL = "https://pulsetrack-back.onrender.com"

def test_mission_creation():
    """Test if mission creation works on Render"""
    
    print("🚀 Testing Mission Creation on Render Backend")
    print(f"⏰ Testing at: {datetime.now().isoformat()}")
    print(f"📍 Backend URL: {BACKEND_URL}\n")
    
    # Test 1: Health check
    print("TEST 1: Health Check")
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/health/", timeout=5)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("✅ Backend is responding\n")
        else:
            print(f"⚠️  Unexpected status: {r.status_code}\n")
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        return False
    
    # Test 2: Create mission
    print("TEST 2: Mission Creation")
    mission_payload = {
        "mission_number": f"TEST-{int(time.time())}",
        "status": "planned",
        "priority": "normal",
        "origin": {
            "name": "Origin",
            "lat": -1.2921,
            "lng": 36.8219
        },
        "destination": {
            "name": "Destination",
            "lat": -1.3011,
            "lng": 36.8142
        },
        "cargo": {
            "description": "Test cargo"
        }
    }
    
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/v1/missions/",
            json=mission_payload,
            timeout=10
        )
        print(f"Status: {r.status_code}")
        
        if r.status_code in [200, 201]:
            response_data = r.json()
            print(f"✅ Mission Created Successfully!")
            print(f"   Mission ID: {response_data.get('id')}")
            print(f"   Mission Number: {response_data.get('mission_number')}")
            print(f"   Distance: {response_data.get('distance_total_m')} m")
            return True
        else:
            print(f"❌ Failed with status {r.status_code}")
            print(f"Response: {r.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ Mission creation failed: {e}\n")
        return False

if __name__ == "__main__":
    print("="*60)
    success = test_mission_creation()
    print("="*60)
    if success:
        print("\n✅ MISSION CREATION WORKING - FIX SUCCESSFUL!")
    else:
        print("\n❌ Mission creation still failing - more debugging needed")
    print("\nNext Steps:")
    print("1. Wait 1-2 minutes for Render to fully deploy")
    print("2. Run this test again")
    print("3. Check Render deployment logs if still failing")
