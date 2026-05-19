#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

from django.urls import resolve
from django.test import RequestFactory

# Test URL resolution
print("=" * 60)
print("TESTING URL RESOLUTION")
print("=" * 60)

try:
    match = resolve('/api/v1/mobile/mission/start-tracking/')
    print(f"URL resolved successfully!")
    print(f"View function: {match.func}")
    print(f"View name: {match.url_name}")
    print(f"App name: {match.app_names}")
except Exception as e:
    print(f"Failed to resolve URL: {e}")

# Test if the view is callable
print("\n" + "=" * 60)
print("TESTING VIEW FUNCTION")
print("=" * 60)

try:
    from server.api.views import mobile_mission_start_tracking
    print(f"Function imported: {mobile_mission_start_tracking}")
    print(f"Callable: {callable(mobile_mission_start_tracking)}")
    print(f"Has cls attr: {hasattr(mobile_mission_start_tracking, 'cls')}")
    
    # Check if it's wrapped by @api_view
    if hasattr(mobile_mission_start_tracking, 'cls'):
        print(f"Wrapped by @api_view: True")
        print(f"Accepted methods: {getattr(mobile_mission_start_tracking, 'actions', 'N/A')}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Try to call the view directly
print("\n" + "=" * 60)
print("TESTING DIRECT VIEW CALL")
print("=" * 60)

try:
    factory = RequestFactory()
    from server.api.models import FleetDriver, FleetMission
    
    driver = FleetDriver.objects.first()
    mission = FleetMission.objects.first()
    
    if driver and mission:
        request = factory.post('/api/v1/mobile/mission/start-tracking/', 
                              {'driver_id': str(driver.id), 'mission_id': str(mission.id)},
                              content_type='application/json')
        
        response = mobile_mission_start_tracking(request)
        print(f"Response status: {response.status_code}")
        print(f"Response successful: {response.status_code == 200}")
    else:
        print("No test data available")
        
except Exception as e:
    print(f"Error calling view: {e}")
    import traceback
    traceback.print_exc()
