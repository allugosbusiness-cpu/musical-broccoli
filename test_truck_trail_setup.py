import django
django.setup()

from server.api.models import FleetTruck, Driver, Mission, TruckLocation
import uuid
from decimal import Decimal

# Create a test truck
truck = FleetTruck.objects.create(
    id=uuid.uuid4(),
    truck_number="TEST-001",
    capacity_kg=5000,
    fuel_type="diesel",
    status="active"
)
print(f"Created truck: {truck.id}")

# Create a test driver
driver = Driver.objects.create(
    id=uuid.uuid4(),
    full_name="Test Driver",
    phone_number="+254712345678",
    license_number="KE-DL-12345",
    status="available"
)
print(f"Created driver: {driver.id}")

# Create some test locations/trail data
for i in range(5):
    TruckLocation.objects.create(
        truck=truck,
        latitude=Decimal("-1.2921") + Decimal(str(i * 0.0001)),
        longitude=Decimal("36.8219") + Decimal(str(i * 0.0001)),
        accuracy=10.5,
        timestamp=None
    )
print(f"Created 5 truck locations")

# Now test the endpoint
from django.test import Client
client = Client()

truck_id = str(truck.id)
print(f"\nTesting truck_trail_with_directions with truck ID: {truck_id}")
response = client.get(f"/api/v1/trucks/{truck_id}/truck_trail_with_directions/?limit=100")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Trail count: {data.get('count', 0)}")
    print(f"Response keys: {list(data.keys())}")
    print(f"Data: {data}")
else:
    print(f"Error: {response.content}")
