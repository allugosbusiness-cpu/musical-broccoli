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
from .delivery_endpoints import (
    mission_delivery_confirmed, driver_status, mission_details
)
from .fuel_views import (
    TruckFuelViewSet, FuelConsumptionViewSet, FuelAlertViewSet, FuelReportViewSet
)

# Try to import from server.api if available, otherwise create placeholder
try:
    from server.api.activities_endpoints import get_activities, get_activity_summary
except ImportError:
    # Fallback: define simple activities endpoints inline
    from django.http import JsonResponse
    from django.utils import timezone
    from datetime import timedelta
    from api.models_v2 import FleetActivity
    
    def get_activities(request):
        """Retrieve activities from audit trail"""
        try:
            days = int(request.GET.get('days', 7))
            limit = int(request.GET.get('limit', 50))
            start_date = timezone.now() - timedelta(days=days)
            query = FleetActivity.objects.filter(timestamp__gte=start_date)[:limit]
            activities_data = [{
                'id': str(a.id),
                'truck_identifier': a.truck.truck_identifier if a.truck else None,
                'activity_type': a.activity_type,
                'timestamp': a.timestamp.isoformat(),
            } for a in query]
            return JsonResponse({'activities': activities_data, 'total_count': len(activities_data)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def get_activity_summary(request):
        """Get activity summary statistics"""
        try:
            days = int(request.GET.get('days', 7))
            start_date = timezone.now() - timedelta(days=days)
            query = FleetActivity.objects.filter(timestamp__gte=start_date)
            return JsonResponse({'total_count': query.count()})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

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
router_v1.register(r'alerts', AlertViewSet, basename='alert-v1')
router_v1.register(r'fuel-alerts', FuelAlertViewSet, basename='fuel-alert-v1')
router_v1.register(r'fuel', TruckFuelViewSet, basename='fuel-v1')
router_v1.register(r'fuel-consumption', FuelConsumptionViewSet, basename='fuel-consumption-v1')
router_v1.register(r'fuel-reports', FuelReportViewSet, basename='fuel-report-v1')

urlpatterns = [
    path('', include(router.urls)),
    path('v1/', include(router_v1.urls)),
    path('v1/calculate-distance/', calculate_distance, name='calculate-distance'),
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
    # Activity tracking endpoints
    path('v1/activities/', get_activities, name='activities'),
    path('v1/activities/summary/', get_activity_summary, name='activities-summary'),
]
