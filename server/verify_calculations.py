#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.dashboard_service import get_missions_with_details, get_trucks_with_mission_data
import json

print('=== MISSIONS WITH DISTANCE & PROGRESS ===')
missions = get_missions_with_details()
for m in missions:
    print(f"Mission {m['mission_number']}: {m['progress_pct']:.1f}% progress, {m['distance_total_m']/1000:.1f}km distance")

print('\n=== TRUCKS WITH TOTAL DISTANCE ===')
trucks = get_trucks_with_mission_data()
for t in trucks:
    print(f"Truck {t['truck_identifier']}: {t['distance_travelled_km']:.1f}km distance, {t['fuel_consumed_liters']:.1f}L fuel")
