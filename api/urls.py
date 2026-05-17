from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DriverViewSet, TruckViewSet, MissionViewSet,
    MissionDisputeViewSet, DriverPerformanceViewSet, CheckpointViewSet,
    dashboard_summary, drivers_list_with_performance,
    trucks_list_with_mission_data, missions_list_with_details,
    recalculate_performance, sync_truck_data,
    mission_route_geometry, alert_list,
    update_truck_location_speed, get_truck_current_location_speed,
    get_all_trucks_current_locations
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
    # Dashboard
    path('v1/dashboard/summary/', dashboard_summary),
    path('v1/dashboard/drivers/', drivers_list_with_performance),
    path('v1/dashboard/trucks/', trucks_list_with_mission_data),
    path('v1/dashboard/missions/', missions_list_with_details),
    path('v1/dashboard/missions/<str:mission_id>/route-geometry/', mission_route_geometry),
    path('v1/dashboard/recalculate-percentage/', recalculate_performance),
    path('v1/dashboard/sync-truck-data/', sync_truck_data),
    # Alert
    path('v1/alerts/', alert_list),
    # Truck Tracking (V2 API)
    path('v1/truck-tracking/location-speed/', update_truck_location_speed),
    path('v1/truck-tracking/location-speed/<str:truck_id>/', get_truck_current_location_speed),
    path('v1/truck-tracking/all-locations/', get_all_trucks_current_locations),
]
