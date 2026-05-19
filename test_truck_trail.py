import django
django.setup()

from django.test import Client
from server.api.models import FleetTruck

client = Client()

# Get a truck
truck = FleetTruck.objects.first()
if truck:
    truck_id = str(truck.id)
    print(f"Testing truck_trail_with_directions with truck ID: {truck_id}")
    response = client.get(f"/api/v1/trucks/{truck_id}/truck_trail_with_directions/?limit=100")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Trail count: {data.get('count', 0)}")
    print(f"Response keys: {list(data.keys())}")
    print(f"Data sample: {str(data)[:300]}")
else:
    print("No trucks found")
