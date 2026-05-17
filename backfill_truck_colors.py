#!/usr/bin/env python
"""
Backfill truck colors for all existing trucks
Run: pipenv run python backfill_truck_colors.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.models import Truck
from api.color_utils import generate_truck_color

def backfill_colors():
    """Assign unique colors to all trucks"""
    trucks = Truck.objects.all()
    updated_count = 0
    
    for truck in trucks:
        try:
            # Generate deterministic color based on truck ID
            color = generate_truck_color(str(truck.id))
            
            if truck.route_color != color:
                truck.route_color = color
                truck.save()
                print(f"✅ {truck.id} ({truck.plate}) → {color}")
                updated_count += 1
            else:
                print(f"⏭️  {truck.id} ({truck.plate}) already has {color}")
        except Exception as e:
            print(f"❌ Error updating {truck.id}: {e}")
    
    print(f"\n✨ Backfill complete! Updated {updated_count} trucks")

if __name__ == '__main__':
    backfill_colors()
