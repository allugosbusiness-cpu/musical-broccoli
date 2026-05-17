import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.models import Truck
from api.data_locations import GLOBAL_LOCATIONS

# Sample truck data
sample_trucks = [
    {
        'id': 'TRUCK-001',
        'plate': 'ZWE-2024-001',
        'driver': 'John Ndlela',
        'status': 'moving',
        'location': 'Harare',
        'origin': 'Harare',
        'destination': 'Bulawayo',
        'speed': 85,
        'eta': '2026-04-25 14:00',
        'progress': 45,
        'cargo': 'Electronics',
        'weight': '2500kg',
        'distance_travelled': 150,
        'total_distance': 330,
        'coordinates': GLOBAL_LOCATIONS['Harare'],
        'origin_coordinates': GLOBAL_LOCATIONS['Harare'],
        'destination_coordinates': GLOBAL_LOCATIONS['Bulawayo'],
    },
    {
        'id': 'TRUCK-002',
        'plate': 'ZWE-2024-002',
        'driver': 'Grace Mwale',
        'status': 'moving',
        'location': 'Bulawayo',
        'origin': 'Harare',
        'destination': 'Mutare',
        'speed': 92,
        'eta': '2026-04-25 18:30',
        'progress': 62,
        'cargo': 'FMCG',
        'weight': '3200kg',
        'distance_travelled': 210,
        'total_distance': 340,
        'coordinates': GLOBAL_LOCATIONS['Bulawayo'],
        'origin_coordinates': GLOBAL_LOCATIONS['Harare'],
        'destination_coordinates': GLOBAL_LOCATIONS['Mutare'],
    },
    {
        'id': 'TRUCK-003',
        'plate': 'ZWE-2024-003',
        'driver': 'Tendai Munodawafa',
        'status': 'delayed',
        'location': 'Chitungwiza',
        'origin': 'Johannesburg',
        'destination': 'Harare',
        'speed': 45,
        'eta': '2026-04-26 10:15',
        'progress': 28,
        'cargo': 'Pharmaceuticals',
        'weight': '1800kg',
        'distance_travelled': 95,
        'total_distance': 340,
        'coordinates': GLOBAL_LOCATIONS['Chitungwiza'],
        'origin_coordinates': GLOBAL_LOCATIONS['Johannesburg'],
        'destination_coordinates': GLOBAL_LOCATIONS['Harare'],
    },
    {
        'id': 'TRUCK-004',
        'plate': 'ZWE-2024-004',
        'driver': 'Mpilo Dlamini',
        'status': 'moving',
        'location': 'Mutare',
        'origin': 'Bulawayo',
        'destination': 'Mutare',
        'speed': 110,
        'eta': '2026-04-24 22:45',
        'progress': 85,
        'cargo': 'Agriculture',
        'weight': '5000kg',
        'distance_travelled': 280,
        'total_distance': 330,
        'coordinates': GLOBAL_LOCATIONS['Mutare'],
        'origin_coordinates': GLOBAL_LOCATIONS['Bulawayo'],
        'destination_coordinates': GLOBAL_LOCATIONS['Mutare'],
    },
    {
        'id': 'TRUCK-005',
        'plate': 'ZWE-2024-005',
        'driver': 'Thembi Nkosi',
        'status': 'delivered',
        'location': 'Harare',
        'origin': 'Lusaka',
        'destination': 'Harare',
        'speed': 0,
        'eta': '2026-04-24 12:00',
        'progress': 100,
        'cargo': 'Fuel Tanks',
        'weight': '4500kg',
        'distance_travelled': 320,
        'total_distance': 320,
        'coordinates': GLOBAL_LOCATIONS['Harare'],
        'origin_coordinates': GLOBAL_LOCATIONS['Lusaka'],
        'destination_coordinates': GLOBAL_LOCATIONS['Harare'],
    },
]

# Clear existing trucks
Truck.objects.all().delete()
print("✓ Cleared existing trucks")

# Add sample trucks
for truck_data in sample_trucks:
    truck = Truck.objects.create(**truck_data)
    print(f"✓ Created truck: {truck.id} ({truck.driver}) - {truck.status.upper()}")
    print(f"  Route: {truck.origin} → {truck.destination}")

print("\n✓ Sample data added successfully!")
