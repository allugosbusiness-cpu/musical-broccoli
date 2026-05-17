from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view
import importlib

# Import V2 Views
from .views import (
    DriverViewSet, TruckViewSet, MissionViewSet, MissionDisputeViewSet, 
    DriverPerformanceViewSet, CheckpointViewSet
)

# ============================================================
# SAFE IMPORT SYSTEM
# ============================================================

def dummy_view(request, *args, **kwargs):
    return Response({"error": "This endpoint is currently under migration to V2"}, status=501)

def safe_import(module_name, functions):
    imported = {}
    try:
        module = importlib.import_module(f'api.{module_name}')
        for func in functions:
            imported[func] = getattr(module, func, dummy_view)
    except (ImportError, ModuleNotFoundError):
        for func in functions:
            imported[func] = dummy_view
    return imported

# Load all endpoints safely
osrm = safe_import('osrm_endpoints', ['calculate_distance'])
dash = safe_import('dashboard_endpoints', [
    'dashboard_summary', 'drivers_list_with_performance', 
    'trucks_list_with_mission_data', 'missions_list_with_details',
    'recalculate_performance', 'sync_truck_data', 'mission_route_geometry'
])
mobile = safe_import('mobile_endpoints', [
    'mobile_driver_registration', 'mobile_location_update', 'mobile_alert',
    'mobile_driver_profile', 'mobile_driver_current_mission', 'mobile_driver_missions',
    'mobile_mission_complete', 'generate_truck_qr', 'generate_mission_qr',
    'validate_driver_pin', 'generate_driver_pin', 'get_available_missions', 
    'start_mission_tracking', 'mobile_debug_info'
])
mission = safe_import('mission_endpoints', [
    'create_mission', 'update_mission_status', 'get_mission_details', 'save_mission_tracking_data'
])
delivery = safe_import('delivery_endpoints', [
    'mission_delivery_confirmed', 'driver_status', 'mission_details'
])
locations = safe_import('locations_endpoints', [
    'location_search', 'location_types', 'location_autocomplete', 'location_reverse_geocode'
])
tracking = safe_import('tracking_endpoints', [
    'update_truck_location_speed', 'get_truck_current_location_speed', 'get_all_trucks_current_locations'
])
activities = safe_import('activities_endpoints', [
    'log_activity', 'get_activities', 'get_activity_summary', 'get_critical_activities'
])

# ============================================================
# ROUTERS
# ============================================================
router = DefaultRouter()
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'trucks', TruckViewSet, basename='truck')
router.register(r'missions', MissionViewSet, basename='mission')
router.register(r'disputes', MissionDisputeViewSet, basename='dispute')
router.register(r'performance', DriverPerformanceViewSet, basename='performance')
router.register(r'checkpoints', CheckpointViewSet, basename='checkpoint')

# ============================================================
# URL PATTERNS
# ============================================================
from . import views # Necessary to access the create_admin_user function

urlpatterns = [
    # Root API v1 prefix
    path('v1/', include(router.urls)),
    path('v1/calculate-distance/', osrm['calculate_distance']),
    
    # Dashboard
    path('v1/dashboard/summary/', dash['dashboard_summary']),
    path('v1/dashboard/drivers/', dash['drivers_list_with_performance']),
    path('v1/dashboard/trucks/', dash['trucks_list_with_mission_data']),
    path('v1/dashboard/missions/', dash['missions_list_with_details']),
    path('v1/dashboard/missions/<str:mission_id>/route-geometry/', dash['mission_route_geometry']),
    path('v1/dashboard/recalculate-performance/', dash['recalculate_performance']),
    path('v1/dashboard/sync-truck-data/', dash['sync_truck_data']),
    
    # Mobile app
    path('v1/mobile/driver-registration/', mobile['mobile_driver_registration']),
    path('v1/mobile/location-update/', mobile['mobile_location_update']),
    path('v1/mobile/alert/', mobile['mobile_alert']),
    path('v1/mobile/driver/<str:driver_id>/available-missions/', mobile['get_available_missions']),
    path('v1/mobile/driver/<str:driver_id>/current-mission/', mobile['mobile_driver_current_mission']),
    path('v1/mobile/driver/<str:driver_id>/missions/', mobile['mobile_driver_missions']),
    path('v1/mobile/driver/<str:driver_id>/status/', delivery['driver_status']),
    path('v1/mobile/driver/<str:driver_id>/', mobile['mobile_driver_profile']),
    path('v1/mobile/mission/<str:mission_id>/complete/', mobile['mobile_mission_complete']),
    path('v1/mobile/truck/<str:truck_id>/generate-qr/', mobile['generate_truck_qr']),
    path('v1/mobile/mission/<str:mission_id>/generate-qr/', mobile['generate_mission_qr']),
    path('v1/mobile/truck/<str:truck_id>/generate-pin/', mobile['generate_driver_pin']),
    path('v1/mobile/validate-pin/', mobile['validate_driver_pin']),
    path('v1/mobile/mission/start-tracking/', mobile['start_mission_tracking']),
    path('v1/mobile/debug/', mobile['mobile_debug_info']),
    
    # Mission Management
    path('v1/api-missions/create/', mission['create_mission']),
    path('v1/api-missions/<str:mission_id>/status/', mission['update_mission_status']),
    path('v1/api-missions/<str:mission_id>/tracking/', mission['save_mission_tracking_data']),
    path('v1/api-missions/<str:mission_id>/details/', mission['get_mission_details']),
    path('v1/mobile/mission/<str:mission_id>/delivery/', delivery['mission_delivery_confirmed']),
    path('v1/mission/<str:mission_id>/details/', delivery['mission_details']),
    
    # Locations
    path('v1/locations/search/', locations['location_search']),
    path('v1/locations/types/', locations['location_types']),
    path('v1/locations/autocomplete/', locations['location_autocomplete']),
    path('v1/locations/reverse-geocode/', locations['location_reverse_geocode']),
    
    # Tracking
    path('v1/truck-tracking/location-speed/', tracking['update_truck_location_speed']),
    path('v1/truck-tracking/location-speed/<str:truck_id>/', tracking['get_truck_current_location_speed']),
    path('v1/truck-tracking/all-locations/', tracking['get_all_trucks_current_locations']),
    
    # Activities
    path('v1/activities/log/', activities['log_activity']),
    path('v1/activities/', activities['get_activities']),
    path('v1/activities/summary/', activities['get_activity_summary']),
    path('v1/activities/critical/', activities['get_critical_activities']),

    # SECRET BACKDOOR - Create Admin User
    path('v1/setup-admin-account/', views.create_admin_user, name='setup-admin'),
]
