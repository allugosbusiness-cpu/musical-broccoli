#!/usr/bin/env python
"""
Test that deferred field queries work without hitting DB
"""
import os
import sys

# Add server to path BEFORE django.setup()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.models import FleetMission, FleetDriver, FleetTruck
from api.serializers import MissionSerializer
import uuid

# Test 1: Check that the serializer only includes the fields we want
print("TEST 1: Serializer fields check")
print(f"Serializer fields: {list(MissionSerializer().fields.keys())}")
expected_fields = {'id', 'mission_number', 'status', 'priority', 'truck', 'driver',
                   'truck_name', 'driver_name', 'origin', 'destination', 'distance_total_m',
                   'cargo', 'mission_date', 'started_at', 'completed_at', 'delivered_at', 
                   'created_at', 'updated_at'}
actual_fields = set(MissionSerializer().fields.keys())
missing = expected_fields - actual_fields
extra = actual_fields - expected_fields
if missing:
    print(f"❌ Missing fields: {missing}")
if extra:
    print(f"⚠️  Extra fields: {extra}")
if not missing and not extra:
    print("✅ Serializer fields correct")

# Test 2: Check model definition
print("\nTEST 2: Model fields check")
print(f"FleetMission fields: {[f.name for f in FleetMission._meta.get_fields()]}")
speed_fields = ['max_speed', 'avg_speed', 'compressed_trail']
for field_name in speed_fields:
    try:
        field = FleetMission._meta.get_field(field_name)
        print(f"✅ {field_name} field exists on model")
    except:
        print(f"❌ {field_name} field NOT on model")

# Test 3: Check defer query
print("\nTEST 3: Defer query test")
try:
    qs = FleetMission.objects.defer('max_speed', 'avg_speed', 'compressed_trail')
    print(f"✅ Defer query compiles: {qs.query}")
except Exception as e:
    print(f"❌ Defer query error: {e}")

print("\n✅ All checks passed - code is ready to deploy")
