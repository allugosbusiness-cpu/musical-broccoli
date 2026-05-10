#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.models import TrackPoint

count = TrackPoint.objects.count()
print(f"Total TrackPoints in DB: {count}")

# Get sample from each truck
from api.models import Truck
trucks = Truck.objects.all()
for truck in trucks:
    tp_count = TrackPoint.objects.filter(truck_id=truck.id).count()
    print(f"  {truck.id}: {tp_count} points")
