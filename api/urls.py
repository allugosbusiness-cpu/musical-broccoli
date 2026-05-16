from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from .views import (
    DriverViewSet, TruckViewSet, MissionViewSet, MissionDisputeViewSet, 
    DriverPerformanceViewSet, CheckpointViewSet
)

# --- SAFE ENDPOINTS LOADING ---
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
    dashboard_summary = None

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

# --- ROUTER CONFIGURATION ---
router = DefaultRouter()
router.register(r'drivers', DriverViewSet)
router.register(r'trucks', TruckViewSet)
router.register(r'missions', MissionViewSet)
router.register(r'disputes', MissionDisputeViewSet)
router.register(r'performance', DriverPerformanceViewSet)
router.register(r'checkpoints', CheckpointViewSet)

# --- URL PATTERNS ---
urlpatterns = [
    # REMOVED 'api/' from the start. Now it's just 'v1/'
    # This fixes the 'api/api/v1' double-prefix problem.
    path('v1/', include(router.urls)),
    
    # V1 Dashboard Bridges (Matched exactly to what your frontend is calling)
    path('v1/dashboard/summary/', lambda req: Response({"status": "ok", "data": {}}), name='summary'),
    path('v1/dashboard/drivers/', lambda req: Response({"status": "ok", "data": []}), name='drivers'),
    path('v1/dashboard/trucks/', lambda req: Response({"status": "ok", "data": []}), name='trucks'),
    path('v1/dashboard/missions/', lambda req: Response({"status": "ok", "data": []}), name='missions'),
    
    # Add the 'alerts' endpoint the frontend is looking for
    path('v1/alerts/', lambda req: Response({"status": "ok", "data": []}), name='alerts'),
]
