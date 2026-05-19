import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

from django.test import Client
from server.api.models import FleetDriver, FleetMission

driver = FleetDriver.objects.first()
mission = FleetMission.objects.first()

print("Testing start_tracking action via router")
print("=" * 60)

client = Client()
# Router creates action URLs at: /basename/{action}/
url = '/api/v1/missions/start-tracking/'
payload = {
    'driver_id': str(driver.id),
    'mission_id': str(mission.id)
}

print(f"URL: {url}")
print(f"Sending POST...")

response = client.post(url, data=json.dumps(payload), content_type='application/json')

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = json.loads(response.content)
    print(f"SUCCESS! Mission status: {data.get('mission', {}).get('status')}")
else:
    print(f"ERROR {response.status_code}")
    print(f"Response: {response.content[:300].decode('utf-8', errors='ignore')}")
