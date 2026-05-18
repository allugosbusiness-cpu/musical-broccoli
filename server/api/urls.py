from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view
import importlib

from .views import (
    DriverViewSet, TruckViewSet, MissionViewSet,
    LocationViewSet, ActivityViewSet, PerformanceViewSet,
    AlertViewSet, health_check, api_root
)

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
        print(f"⚠️  Failed to import {module_name}: {e}")
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
    path('v1/', include(router.urls)),
    # Mobile endpoints (if module exists)
    path('v1/mobile/register/', mobile.get('mobile_driver_registration', dummy_view), name='mobile-register'),
    path('v1/mobile/location/', mobile.get('mobile_location_update', dummy_view), name='mobile-location'),
    path('v1/mobile/profile/', mobile.get('mobile_driver_profile', dummy_view), name='mobile-profile'),
    path('v1/mobile/mission/current/', mobile.get('mobile_driver_current_mission', dummy_view), name='mobile-current-mission'),
    path('v1/mobile/mission/complete/', mobile.get('mobile_mission_complete', dummy_view), name='mobile-complete'),
]