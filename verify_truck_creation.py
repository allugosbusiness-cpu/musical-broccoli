import requests
import json

r = requests.get('https://pulsetrack-back.onrender.com/api/v1/trucks/')
data = r.json()
trucks = data.get('results', [])

print(f"✅ Total trucks on Render backend: {len(trucks)}")
print("\n📋 Most recent trucks:")
recent = sorted(trucks, key=lambda t: t.get('created_at', ''), reverse=True)[:3]
for t in recent:
    print(f"  - {t.get('truck_identifier'):20} | Plate: {t.get('plate'):15} | Created: {t.get('created_at', 'N/A')}")
