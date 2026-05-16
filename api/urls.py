from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DriverViewSet, TruckViewSet, MissionViewSet, MissionDisputeViewSet, 
    DriverPerformanceViewSet, CheckpointViewSet
)
from .new_mission_endpoints import (
    create_mission, update_mission_status, get_mission_details, save_mission_tracking_data
)
from .delivery_endpoints import (
    mission_delivery_confirmed, driver_status, mission_details
)

# Try to import optional endpoints - these may not all exist
try:
    from .osrm_endpoints import calculate_distance
except ImportError:
    calculate_distance = None

try:
    from .dashboard_endpoints import (
        dashboard_summary, drivers_list_with_performance, 
        trucks_list_with_mission_data, missions_list_with_details,
        recalculate_performance, sync_truck_data, mission_route_geometry
    )
except ImportError:
    dashboard_summary = dashboard_endpoints_missing = None

try:
    from .mobile_endpoints import (
        mobile_driver_registration, mobile_location_update, mobile_alert,
        mobile_driver_profile, mobile_driver_current_mission, mobile_driver_missions,
        mobile_mission_complete, generate_truck_qr, generate_mission_qr,
        validate_driver_pin, generate_driver_pin, get_available_missions, 
        start_mission_tracking, mobile_debug_info
    )
except ImportError:
    mobile_driver_registration = None

try:
    from .locations_endpoints import (
        location_search, location_types, location_autocomplete, location_reverse_geocode
    )
except ImportError:
    location_search = None

try:
    from .tracking_endpoints import (
        update_truck_location_speed, get_truck_current_location_speed, get_all_trucks_current_locations
    )
except ImportError:
    update_truck_location_speed = None

try:
    from .activities_endpoints import (
        log_activity, get_activities, get_activity_summary, get_critical_activities
    )
except ImportError:
    log_activity = None

# v2 router (new schema)
router_v2 = DefaultRouter()
router_v2.register(r'drivers', DriverViewSet, basename='driver')
router_v2.register(r'trucks', TruckViewSet, basename='truck')
router_v2.register(r'missions', MissionViewSet, basename='mission')
router_v2.register(r'disputes', MissionDisputeViewSet, basename='dispute')
router_v2.register(r'performance', DriverPerformanceViewSet, basename='performance')
router_v2.register(r'checkpoints', CheckpointViewSet, basename='checkpoint')

urlpatterns = [
    path('v1/', include(router_v2.urls)),
]

# Add optional endpoints only if they were imported successfully
if calculate_distance:
    urlpatterns += [path('v1/calculate-distance/', calculate_distance, name='calculate-distance')]

# Mission management endpoints
urlpatterns += [
    path('v1/api-missions/create/', create_mission, name='create-mission'),
    path('v1/api-missions/<str:mission_id>/status/', update_mission_status, name='update-mission-status'),
    path('v1/api-missions/<str:mission_id>/tracking/', save_mission_tracking_data, name='save-mission-tracking-data'),
    path('v1/api-missions/<str:mission_id>/details/', get_mission_details, name='get-mission-details'),
    
    # Delivery confirmation endpoints
    path('v1/mobile/mission/<str:mission_id>/delivery/', mission_delivery_confirmed, name='mission-delivery-confirmed'),
    path('v1/mission/<str:mission_id>/details/', mission_details, name='mission-details'),
    path('v1/mobile/driver/<str:driver_id>/status/', driver_status, name='driver-status'),
]

# Add dashboard endpoints if available
if dashboard_summary:
    urlpatterns += [
        path('v1/dashboard/summary/', dashboard_summary, name='dashboard-summary'),
        path('v1/dashboard/drivers/', drivers_list_with_performance, name='dashboard-drivers'),
        path('v1/dashboard/trucks/', trucks_list_with_mission_data, name='dashboard-trucks'),
        path('v1/dashboard/missions/', missions_list_with_details, name='dashboard-missions'),
        path('v1/dashboard/missions/<str:mission_id>/route-geometry/', mission_route_geometry, name='mission-route-geometry'),
        path('v1/dashboard/recalculate-performance/', recalculate_performance, name='recalculate-performance'),
        path('v1/dashboard/sync-truck-data/', sync_truck_data, name='sync-truck-data'),
    ]

# Add mobile endpoints if available
if mobile_driver_registration:
    urlpatterns += [
        path('v1/mobile/driver-registration/', mobile_driver_registration, name='mobile-driver-registration'),
        path('v1/mobile/location-update/', mobile_location_update, name='mobile-location-update'),
        path('v1/mobile/alert/', mobile_alert, name='mobile-alert'),
        path('v1/mobile/driver/<str:driver_id>/available-missions/', get_available_missions, name='get-available-missions'),
        path('v1/mobile/driver/<str:driver_id>/current-mission/', mobile_driver_current_mission, name='mobile-driver-current-mission'),
        path('v1/mobile/driver/<str:driver_id>/missions/', mobile_driver_missions, name='mobile-driver-missions'),
        path('v1/mobile/driver/<str:driver_id>/', mobile_driver_profile, name='mobile-driver-profile'),
        path('v1/mobile/mission/<str:mission_id>/complete/', mobile_mission_complete, name='mobile-mission-complete'),
        path('v1/mobile/truck/<str:truck_id>/generate-qr/', generate_truck_qr, name='generate-truck-qr'),
        path('v1/mobile/mission/<str:mission_id>/generate-qr/', generate_mission_qr, name='generate-mission-qr'),
        path('v1/mobile/truck/<str:truck_id>/generate-pin/', generate_driver_pin, name='generate-driver-pin'),
        path('v1/mobile/validate-pin/', validate_driver_pin, name='validate-driver-pin'),
        path('v1/mobile/mission/start-tracking/', start_mission_tracking, name='start-mission-tracking'),
        path('v1/mobile/debug/', mobile_debug_info, name='mobile-debug-info'),
    ]

# Add location endpoints if available
if location_search:
    urlpatterns += [
        path('v1/locations/search/', location_search, name='location-search'),
        path('v1/locations/types/', location_types, name='location-types'),
        path('v1/locations/autocomplete/', location_autocomplete, name='location-autocomplete'),
        path('v1/locations/reverse-geocode/', location_reverse_geocode, name='location-reverse-geocode'),
    ]

# Add tracking endpoints if available
if update_truck_location_speed:
    urlpatterns += [
        path('v1/truck-tracking/location-speed/', update_truck_location_speed, name='update-truck-location-speed'),
        path('v1/truck-tracking/location-speed/<str:truck_id>/', get_truck_current_location_speed, name='get-truck-location-speed'),
        path('v1/truck-tracking/all-locations/', get_all_trucks_current_locations, name='get-all-trucks-locations'),
    ]

# Add activity endpoints if available
if log_activity:
    urlpatterns += [
      # Change your urlpatterns block to this:
urlpatterns = [
    # This makes the new V2 router work with the frontend's /api/v1/ prefix
    path('api/v1/', include(router.urls)), 
    
    # These handle the specific dashboard calls the frontend is making
    path('api/v1/dashboard/summary/', lambda req: Response({"status": "ok", "data": {}}), name='summary'),
    path('api/v1/dashboard/drivers/', lambda req: Response({"status": "ok", "data": []}), name='drivers'),
]

    ]
