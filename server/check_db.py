from api.models_v2 import FleetTruck, FleetDriver

print(f"Trucks in DB: {FleetTruck.objects.count()}")
print(f"Drivers in DB: {FleetDriver.objects.count()}")

# List all trucks
for truck in FleetTruck.objects.all():
    print(f"  - {truck.truck_identifier} ({truck.plate}): {truck.status}")
