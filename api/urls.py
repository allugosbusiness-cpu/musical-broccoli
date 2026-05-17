from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DriverViewSet, TruckViewSet, MissionViewSet, 
    MissionDisputeViewSet, DriverPerformanceViewSet, 
    CheckpointViewSet,
    dashboard_summary, 
    drivers_list_with_performance, 
    trucks_list_with_mission_data, 
    missions_list_with_details,
    recalculate_performance, 
    sync_truck_data, 
    mission_route_geometry,
    mobile_driver_registration, 
    mobile_location_update, 
    mobile_alert,
    mobile_driver_profile, 
    mobile_driver_current_mission, 
    mobile_driver_missions,
    mobile_mission_complete, 
    generate_truck_qr, 
    generate_mission_qr,
    validate_driver_pin, 
    generate_driver_pin, 
    get_available_missions, 
    start_mission_tracking, 
    mobile_debug_info
)

router = DefaultRouter()
router.register(r'drivers', DriverViewSet)
router.register(r'trucks', TruckViewSet)
router.register(r'missions', MissionViewSet)
router.register(r'disputes', MissionDisputeViewSet)
router.register(r'performance', DriverPerformanceViewSet)
router.register(r'checkpoints', CheckpointViewSet)

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/dashboard/summary/', dashboard_summary),
    path('v1/dashboard/drivers/', drivers_list_with_performance),
    path('v1/dashboard/trucks/', trucks_list_with_mission_data),
    path('v1/dashboard/missions/', missions_list_with_details),
    path('v1/dashboard/missions/<str:mission_id>/route-geometry/', mission_route_geometry),
    path('v1/dashboard/recalculate-percentage/', recalculate_performance),
    path('v1/dashboard/sync-truck-data/', sync_truck_data),
    path('v1/mobile/driver-registration/', mobile_driver_registration),
    path('v1/mobile/location-update/', mobile_location_update),
    path('v1/mobile/alert/', mobile_alert),
    path('v1/mobile/driver/<str:driver_id>/available-missions/', get_available_missions),
    path('v1/mobile/driver/<str:driver_id>/current-mission/', mobile_driver_current_mission),
    path('v1/mobile/driver/<str:driver_id>/missions/', mobile_driver_missions),
    path('v1/mobile/driver/<str:driver_id>/complete/', mobile_mission_complete),
    path('v1/mobile/driver/<str:driver_id>/', mobile_driver_profile),
    path('v1/mobile/truck/<str:truck_id>/generate-qr/', generate_truck_qr),
    path('v1/mobile/truck/<str:truck_id>/generate-qr/', generate_mission_qr),
    path('v1/mobile/truck/<str:truck_id>/generate-pin/', generate_driver_pin),
    path('v1/mobile/validate-pin/', validate_driver_pin),
    path('v1/mobile/mission/start-tracking/', start_mission_tracking),
    path('v1/mobile/debug/', mobile_debug_info),
]
