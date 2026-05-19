import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, '.')

django.setup()

from server.api.models import FleetMission
from server.api.serializers import MissionSerializer

missions = FleetMission.objects.select_related('truck', 'driver').all()
print(f'Total missions: {missions.count()}')
if missions:
    serializer = MissionSerializer(missions, many=True)
    print(f'Serialized data OK: {len(serializer.data)} items')
    
    # Show first mission details
    first = serializer.data[0]
    print(f"\nFirst mission sample:")
    print(f"  Mission: {first.get('mission_number')}")
    print(f"  Truck: {first.get('truck_name')}")
    print(f"  Driver: {first.get('driver_name')}")
    print(f"  Status: {first.get('status')}")
    print(f"  Distance: {first.get('distance_total_m')} m")
    
    print("\n✓ Dashboard missions endpoint ready!")
else:
    print('No missions to serialize')
