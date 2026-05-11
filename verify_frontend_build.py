#!/usr/bin/env python3
"""Verify frontend build status and API connectivity"""

import requests
import sys

# Test backend API
print("🔍 Testing Backend API...")
try:
    r = requests.get('https://musical-broccoli-production.up.railway.app/api/v1/dashboard/trucks/')
    trucks = r.json()
    print(f"✅ Backend API OK - returning {len(trucks)} trucks")
    for truck in trucks:
        print(f"   - {truck.get('truck_identifier')}: {truck.get('status')} ({truck.get('plate')})")
except Exception as e:
    print(f"❌ Backend API Error: {e}")
    sys.exit(1)

# Test frontend status
print("\n🌐 Testing Frontend Build...")
try:
    r = requests.get('https://pulsetrack-frontend-henna.vercel.app')
    if r.status_code == 200:
        print(f"✅ Frontend Live (Status {r.status_code})")
        # Check if new build deployed by looking for recent CSS
        if 'backdrop-blur' in r.text or 'gradient-to' in r.text:
            print("✅ Latest styling detected (gradient/backdrop classes found)")
        else:
            print("⚠️  Old styling detected - deployment may be pending")
    else:
        print(f"❌ Frontend Status: {r.status_code}")
except Exception as e:
    print(f"❌ Frontend Error: {e}")

print("\nℹ️  Note: If old styling is shown, Vercel is still building. Check deployment status.")
print("    Visit: https://vercel.com/dashboard to monitor build progress")
