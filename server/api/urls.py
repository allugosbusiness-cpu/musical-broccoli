from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view
import importlib

# Mobile endpoints for driver missions and registration
from .views import (
    DriverViewSet, TruckViewSet, MissionViewSet,
    LocationViewSet, ActivityViewSet, PerformanceViewSet,
    AlertViewSet, health_check, api_root, setup_admin_account,
    dashboard_drivers, dashboard_trucks, dashboard_missions,
    dashboard_summary, dashboard_recalculate_performance,
    truck_tracking_all_locations, calculate_distance,
    mobile_driver_registration, mobile_validate_pin, mobile_get_available_missions,
    mission_start_tracking, mobile_get_current_mission,
    mobile_location_update, truck_trail_with_directions
)
from .mission_endpoints import create_mission, mission_route_geometry
from .locations_endpoints import reverse_geocode, location_autocomplete

router = DefaultRouter()
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'trucks', TruckViewSet, basename='truck')
router.register(r'missions', MissionViewSet, basename='mission')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'performance', PerformanceViewSet, basename='performance')
router.register(r'alerts', AlertViewSet, basename='alert')

def dummy_view(request, *args, **kwargs):
    return Response({"error": "This endpoint is currently under migration to V2"}, status=501)

def safe_import(module_name, functions):
    imported = {}
    try:
        module = importlib.import_module(f'server.api.{module_name}')
        for func in functions:
            imported[func] = getattr(module, func, dummy_view)
    except (ImportError, ModuleNotFoundError) as e:
        print(f"[!] Failed to import {module_name}: {e}")
        for func in functions:
            imported[func] = dummy_view
    return imported

# Load optional endpoints if they exist
mobile = safe_import('mobile_endpoints', [
    'mobile_driver_registration', 'mobile_location_update', 'mobile_alert',
    'mobile_driver_profile', 'mobile_driver_current_mission', 'mobile_driver_missions',
    'mobile_mission_complete', 'generate_truck_qr', 'generate_mission_qr',
    'validate_driver_pin', 'generate_driver_pin', 'get_available_missions', 
    'start_mission_tracking', 'mobile_debug_info'
])

urlpatterns = [
    path('v1/', api_root, name='api-root'),
    path('v1/health/', health_check, name='health-check'),
    # Admin setup endpoint
    path('v1/setup-admin-account/', setup_admin_account, name='setup-admin-account'),
    # Dashboard endpoints (specific, before router)
    path('v1/dashboard/drivers/', dashboard_drivers, name='dashboard-drivers'),
    path('v1/dashboard/trucks/', dashboard_trucks, name='dashboard-trucks'),
    path('v1/dashboard/missions/', dashboard_missions, name='dashboard-missions'),
    path('v1/dashboard/summary/', dashboard_summary, name='dashboard-summary'),
    path('v1/dashboard/recalculate-performance/', dashboard_recalculate_performance, name='dashboard-recalculate-performance'),
    # Truck tracking endpoints (specific, before router)
    path('v1/truck-tracking/all-locations/', truck_tracking_all_locations, name='truck-tracking-all-locations'),
    path('v1/trucks/<str:truck_id>/truck_trail_with_directions/', truck_trail_with_directions, name='truck-trail-with-directions'),
    path('v1/calculate-distance/', calculate_distance, name='calculate-distance'),
    # Route geometry endpoint (for GlobalMap to show OSRM routes per mission)
    path('v1/dashboard/missions/<str:mission_id>/route-geometry/', mission_route_geometry, name='dashboard-mission-route-geometry'),
    # Mobile endpoints (specific, before router)
    path('v1/mobile/driver-registration/', mobile_driver_registration, name='mobile-driver-registration'),
    path('v1/mobile/validate-pin/', mobile_validate_pin, name='mobile-validate-pin'),
    path('v1/mobile/driver/<str:driver_id>/available-missions/', mobile_get_available_missions, name='mobile-available-missions'),
    path('v1/mobile/driver/<str:driver_id>/current-mission/', mobile_get_current_mission, name='mobile-current-mission'),
    path('v1/mobile/driver/<str:driver_id>/location/', mobile_location_update, name='mobile-location-update'),
    path('v1/mobile/mission/start-tracking/', mission_start_tracking, name='mobile-mission-start-tracking'),
    # Fallback: also support phone_number-based mission lookup
    path('v1/mobile/missions/by-phone/<str:phone>/', mobile_get_available_missions, name='mobile-missions-by-phone'),
    # Legacy mobile endpoints (if module exists)
    path('v1/mobile/register/', mobile.get('mobile_driver_registration', dummy_view), name='mobile-register'),
    path('v1/mobile/location/', mobile.get('mobile_location_update', dummy_view), name='mobile-location'),
    path('v1/mobile/profile/', mobile.get('mobile_driver_profile', dummy_view), name='mobile-profile'),
    path('v1/mobile/mission/current/', mobile.get('mobile_driver_current_mission', dummy_view), name='mobile-current-mission'),
    path('v1/mobile/mission/complete/', mobile.get('mobile_mission_complete', dummy_view), name='mobile-complete'),
    # Location endpoints (OSM autocomplete and reverse geocode)
    path('v1/locations/autocomplete/', location_autocomplete, name='location-autocomplete'),
    path('v1/locations/reverse-geocode/', reverse_geocode, name='location-reverse-geocode'),
    # Router patterns (generic, after specific paths)
    path('v1/', include(router.urls)),
]