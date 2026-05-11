#!/usr/bin/env python3
import requests
import json

r = requests.get('https://musical-broccoli-production.up.railway.app/api/v1/dashboard/trucks/')
trucks = r.json()

print(f"✅ Status: {r.status_code}")
print(f"✅ Data Type: {type(trucks).__name__}")
print(f"✅ Truck Count: {len(trucks)}")
print(f"\nTrucks:")
for truck in trucks:
    print(f"  - {truck['truck_identifier']}: {truck['status']} ({truck['plate']})")
