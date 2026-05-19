import os, sys, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

from server.api.models import FleetTruck, FleetDriver
from django.test import Client

# Create a truck
truck = FleetTruck.objects.create(
    truck_identifier='TEST-TRUCK-1',
    plate='TEST001',
    status='active'
)

# Create a driver
driver = FleetDriver.objects.create(
    first_name='Test',
    last_name='Driver',
    phone_number='1234567890',
    status='active'
)

print('Created truck:', truck.id)
print('Created driver:', driver.id)

# Now test mission creation
mission_data = {
    'mission_number': 'TEST-LOCAL-MISSION',
    'status': 'planned',
    'truck': str(truck.id),
    'driver': str(driver.id),
    'origin': {'name': 'Origin', 'lat': -1.2921, 'lng': 36.8219},
    'destination': {'name': 'Dest', 'lat': -1.2850, 'lng': 36.8270},
    'priority': 'normal'
}

client = Client()
response = client.post('/api/v1/missions/', json.dumps(mission_data), content_type='application/json')
print('Mission Status:', response.status_code)
content = response.content.decode()
if response.status_code == 201:
    data = json.loads(content)
    print('Mission created:', data.get('mission_number'))
    print('Distance:', data.get('distance_total_m'), 'm')
else:
    print('Error:', content[:800])
