import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from server.api.models_v2 import FleetTruck

trucks = FleetTruck.objects.all().values('truck_identifier', 'plate').order_by('truck_identifier')
print("Current trucks in database:")
print(f"{'Truck Identifier':<20} | {'Plate':<15}")
print("-" * 40)
for truck in trucks:
    print(f"{truck['truck_identifier']:<20} | {truck['plate']:<15}")
print(f"\nTotal: {trucks.count()} trucks")
