import os
import sys
import django
from decimal import Decimal
from math import radians, cos, sin, asin, sqrt

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

print("="*70)
print("DISTANCE CALCULATION TEST - Direct Method Execution")
print("="*70)

# Test data
test_cases = [
    {
        'name': 'Harare to Bulawayo',
        'origin': {'lat': -17.8252, 'lon': 31.0335},
        'destination': {'lat': -20.1551, 'lon': 28.5679}
    },
    {
        'name': 'Using lat/lng keys',
        'origin': {'lat': -17.8252, 'lng': 31.0335},
        'destination': {'lat': -20.1551, 'lng': 28.5679}
    },
    {
        'name': 'Using latitude/longitude keys',
        'origin': {'latitude': -17.8252, 'longitude': 31.0335},
        'destination': {'latitude': -20.1551, 'longitude': 28.5679}
    },
]

def calculate_distance_direct(origin, destination):
    """Direct calculation without serializer"""
    if not origin or not destination:
        return Decimal('0')
    
    lat1 = float(origin.get('lat', origin.get('latitude', 0)))
    lon1 = float(origin.get('lon', origin.get('lng', origin.get('longitude', 0))))
    lat2 = float(destination.get('lat', destination.get('latitude', 0)))
    lon2 = float(destination.get('lon', destination.get('lng', destination.get('longitude', 0))))
    
    print(f"  Coords: lat1={lat1}, lon1={lon1}, lat2={lat2}, lon2={lon2}")
    
    if lat1 == 0 or lon1 == 0 or lat2 == 0 or lon2 == 0:
        print(f"  ❌ Coordinate validation FAILED: returning 0")
        return Decimal('0')
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    meters = km * 1000
    
    return Decimal(str(round(meters, 2)))

for test in test_cases:
    print(f"\n{test['name']}:")
    distance = calculate_distance_direct(test['origin'], test['destination'])
    print(f"  Distance: {distance} meters = {float(distance)/1000:.2f} km")

# Now test through the actual serializer
print("\n" + "="*70)
print("SERIALIZER TEST")
print("="*70)

from server.api.serializers import MissionSerializer
from server.api.models import FleetMission, FleetTruck, FleetDriver

serializer = MissionSerializer()

origin = {'lat': -17.8252, 'lon': 31.0335, 'name': 'Harare'}
destination = {'lat': -20.1551, 'lon': 28.5679, 'name': 'Bulawayo'}

distance = serializer._calculate_distance(origin, destination)
print(f"\nSerializer._calculate_distance() result: {distance} meters")
print(f"Calculated distance: {float(distance)/1000:.2f} km")

if float(distance) == 0:
    print("❌ Serializer is returning 0!")
else:
    print("✓ Serializer distance calculation appears to be working!")
