from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TruckViewSet, CheckpointViewSet, CargoViewSet, AlertViewSet, 
    KPIViewSet, RouteViewSet, LocationViewSet, CurrentLocationViewSet,
    RouteOptimizationViewSet
)
from .views_v2 import (
    DriverViewSet as DriverViewSetV2, TruckViewSet as TruckViewSetV2,
    MissionViewSet, MissionDisputeViewSet, DriverPerformanceViewSet
)
from .osrm_endpoints import calculate_distance
from .dashboard_endpoints import (
    dashboard_summary, drivers_list_with_performance, 
    trucks_list_with_mission_data, missions_list_with_details,
    recalculate_performance, sync_truck_data, mission_route_geometry
)
from .mobile_endpoints import (
    mobile_driver_registration, mobile_location_update, mobile_alert,
    mobile_driver_profile, mobile_driver_current_mission, mobile_driver_missions,
    mobile_mission_complete, generate_truck_qr, generate_mission_qr,
    validate_driver_pin, generate_driver_pin
)
from .mission_endpoints import (
    create_mission, update_mission_status, get_mission_details, save_mission_tracking_data
)
from .delivery_endpoints import (
    mission_delivery_confirmed, driver_status, mission_details
)
from .locations_endpoints import (
    location_search, location_types, location_autocomplete
)
from .tracking_endpoints import (
    update_truck_location_speed, get_truck_current_location_speed, get_all_trucks_current_locations
)
from .fuel_views import (
    TruckFuelViewSet, FuelConsumptionViewSet, FuelAlertViewSet, FuelReportViewSet
)

# Legacy router (v0)
router = DefaultRouter()
router.register(r'trucks', TruckViewSet, basename='truck')
router.register(r'checkpoints', CheckpointViewSet, basename='checkpoint')
router.register(r'cargo', CargoViewSet, basename='cargo')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'kpis', KPIViewSet, basename='kpi')
router.register(r'routes', RouteViewSet, basename='route')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'current-locations', CurrentLocationViewSet, basename='current-location')
router.register(r'route-optimizations', RouteOptimizationViewSet, basename='route-optimization')
router.register(r'fuel', TruckFuelViewSet, basename='fuel')
router.register(r'fuel-consumption', FuelConsumptionViewSet, basename='fuel-consumption')
router.register(r'fuel-alerts', FuelAlertViewSet, basename='fuel-alert')
router.register(r'fuel-reports', FuelReportViewSet, basename='fuel-report')

# v1 router (new schema)
router_v1 = DefaultRouter()
router_v1.register(r'drivers', DriverViewSetV2, basename='driver-v1')
router_v1.register(r'trucks', TruckViewSetV2, basename='truck-v1')
router_v1.register(r'missions', MissionViewSet, basename='mission')
router_v1.register(r'disputes', MissionDisputeViewSet, basename='dispute')
router_v1.register(r'performance', DriverPerformanceViewSet, basename='performance')

urlpatterns = [
    path('', include(router.urls)),
    path('v1/', include(router_v1.urls)),
    path('v1/calculate-distance/', calculate_distance, name='calculate-distance'),
    
    # ✅ Mission management endpoints (custom paths to avoid router conflicts)
    path('v1/api-missions/create/', create_mission, name='create-mission'),
    path('v1/api-missions/<str:mission_id>/status/', update_mission_status, name='update-mission-status'),
    path('v1/api-missions/<str:mission_id>/tracking/', save_mission_tracking_data, name='save-mission-tracking-data'),
    path('v1/api-missions/<str:mission_id>/details/', get_mission_details, name='get-mission-details'),
    
    # Location suggestions endpoints
    path('v1/locations/search/', location_search, name='location-search'),
    path('v1/locations/types/', location_types, name='location-types'),
    path('v1/locations/autocomplete/', location_autocomplete, name='location-autocomplete'),
    
    # Truck location and speed tracking endpoints (real-time from mobile app)
    path('v1/truck-tracking/location-speed/', update_truck_location_speed, name='update-truck-location-speed'),
    path('v1/truck-tracking/location-speed/<str:truck_id>/', get_truck_current_location_speed, name='get-truck-location-speed'),
    path('v1/truck-tracking/all-locations/', get_all_trucks_current_locations, name='get-all-trucks-locations'),
    
    # Dashboard endpoints
    path('v1/dashboard/summary/', dashboard_summary, name='dashboard-summary'),
    path('v1/dashboard/drivers/', drivers_list_with_performance, name='dashboard-drivers'),
    path('v1/dashboard/trucks/', trucks_list_with_mission_data, name='dashboard-trucks'),
    path('v1/dashboard/missions/', missions_list_with_details, name='dashboard-missions'),
    path('v1/dashboard/missions/<str:mission_id>/route-geometry/', mission_route_geometry, name='mission-route-geometry'),
    path('v1/dashboard/recalculate-performance/', recalculate_performance, name='recalculate-performance'),
    path('v1/dashboard/sync-truck-data/', sync_truck_data, name='sync-truck-data'),
    # Mobile app endpoints
    path('v1/mobile/driver-registration/', mobile_driver_registration, name='mobile-driver-registration'),
    path('v1/mobile/location-update/', mobile_location_update, name='mobile-location-update'),
    path('v1/mobile/alert/', mobile_alert, name='mobile-alert'),
    path('v1/mobile/driver/<str:driver_id>/', mobile_driver_profile, name='mobile-driver-profile'),
    path('v1/mobile/driver/<str:driver_id>/current-mission/', mobile_driver_current_mission, name='mobile-driver-current-mission'),
    path('v1/mobile/driver/<str:driver_id>/missions/', mobile_driver_missions, name='mobile-driver-missions'),
    path('v1/mobile/mission/<str:mission_id>/complete/', mobile_mission_complete, name='mobile-mission-complete'),
    path('v1/mobile/truck/<str:truck_id>/generate-qr/', generate_truck_qr, name='generate-truck-qr'),
    path('v1/mobile/mission/<str:mission_id>/generate-qr/', generate_mission_qr, name='generate-mission-qr'),
    path('v1/mobile/truck/<str:truck_id>/generate-pin/', generate_driver_pin, name='generate-driver-pin'),
    path('v1/mobile/validate-pin/', validate_driver_pin, name='validate-driver-pin'),
    # Delivery confirmation endpoints
    path('v1/mobile/mission/<str:mission_id>/delivery/', mission_delivery_confirmed, name='mission-delivery-confirmed'),
    path('v1/mobile/driver/<str:driver_id>/status/', driver_status, name='driver-status'),
    path('v1/mission/<str:mission_id>/details/', mission_details, name='mission-details'),
]
