#!/usr/bin/env python
"""Check if GPS trail data was saved"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.models import TrackPoint, Truck

print("=" * 60)
print("GPS TRAIL DATA VERIFICATION")
print("=" * 60)

total_points = TrackPoint.objects.count()
print(f"\n📊 Total TrackPoints in database: {total_points}")

for truck in Truck.objects.all():
    count = TrackPoint.objects.filter(truck_id=truck.id).count()
    print(f"   {truck.id} ({truck.plate}): {count} points")

if total_points > 0:
    # Get sample data
    print("\n📍 Sample TrackPoint (most recent):")
    latest = TrackPoint.objects.latest('recorded_at')
    print(f"   Truck: {latest.truck_id}")
    print(f"   Lat: {latest.latitude}, Lng: {latest.longitude}")
    print(f"   Speed: {latest.speed} km/h")
    print(f"   Time: {latest.recorded_at}")
