#!/usr/bin/env python
"""Test the production mission start-tracking endpoint"""

import requests
import json

url = "https://pulsetrack-back.onrender.com/api/v1/mobile/mission/start-tracking/"
headers = {
    'Content-Type': 'application/json',
}

payload = {
    'driver_id': '719b3a37-b4e0-4355-8b3f-038741647741',
    'mission_id': '01f1c90c-d487-4785-8cff-a57a80fe84e5'
}

print("=" * 60)
print("Testing Production Mission Start-Tracking Endpoint")
print("=" * 60)
print(f"URL: {url}")
print(f"Headers: {headers}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    # Test OPTIONS first
    print("\n[1] Testing OPTIONS...")
    resp = requests.options(url)
    print(f"Status: {resp.status_code}")
    print(f"Allow header: {resp.headers.get('Allow', 'Not found')}")

    # Test GET
    print("\n[2] Testing GET...")
    resp = requests.get(url)
    print(f"Status: {resp.status_code}")

    # Test POST with empty body
    print("\n[3] Testing POST with empty body...")
    resp = requests.post(url, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:200]}")

    # Test POST with payload
    print("\n[4] Testing POST with payload...")
    resp = requests.post(url, headers=headers, json=payload)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"SUCCESS! Response:")
        data = resp.json()
        print(f"  Mission: {data.get('mission', {}).get('mission_number')}")
        print(f"  Status: {data.get('mission', {}).get('status')}")
    else:
        print(f"FAILED! Response: {resp.text[:200]}")

except Exception as e:
    print(f"ERROR: {str(e)}")
