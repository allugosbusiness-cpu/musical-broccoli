import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

from server.api.models import FleetMission

print("="*70)
print("CHECKING RECENT MISSIONS IN DATABASE")
print("="*70)

missions = FleetMission.objects.order_by('-created_at')[:5]

for mission in missions:
    print(f"\nMission: {mission.mission_number}")
    print(f"  ID: {mission.id}")
    print(f"  Origin: {mission.origin}")
    print(f"  Destination: {mission.destination}")
    print(f"  Distance: {mission.distance_total_m} meters")
    
    # Check if coordinates exist
    origin_has_coords = mission.origin and ('lat' in mission.origin or 'latitude' in mission.origin)
    dest_has_coords = mission.destination and ('lat' in mission.destination or 'latitude' in mission.destination)
    
    if origin_has_coords and dest_has_coords:
        print(f"  ✓ Coordinates are stored in database")
    else:
        print(f"  ❌ Coordinates NOT stored in database!")
        print(f"     Origin has coords: {origin_has_coords}")
        print(f"     Destination has coords: {dest_has_coords}")
