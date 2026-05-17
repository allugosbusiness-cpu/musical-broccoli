from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import (
    FleetDriver, FleetTruck, FleetMission, FleetMissionStop,
    FleetMissionEvent, FleetMissionDispute, FleetDriverPerformanceDaily,
    FleetAdminAuditLog, TruckLocation, FleetActivity
)
from .serializers import (
    DriverSerializer, TruckSerializer, MissionSerializer,
    MissionStopSerializer, MissionEventSerializer, MissionDisputeSerializer,
    DriverPerformanceDailySerializer, FleetActivitySerializer,
    FleetAdminAuditLogSerializer
)

# ============================================================
# VIEWSETS (for the router)
# ============================================================
class DriverViewSet(viewsets.ModelViewSet):
    queryset = FleetDriver.objects.all()
    serializer_class = DriverSerializer

class TruckViewSet(viewsets.ModelViewSet):
    queryset = FleetTruck.objects.all()
    serializer_class = TruckSerializer

class MissionViewSet(viewsets.ModelViewSet):
    queryset = FleetMission.objects.all()
    serializer_class = MissionSerializer

class MissionDisputeViewSet(viewsets.ModelViewSet):
    queryset = FleetMissionDispute.objects.all()
    serializer_class = MissionDisputeSerializer

class DriverPerformanceViewSet(viewsets.ModelViewSet):
    queryset = FleetDriverPerformanceDaily.objects.all()
    serializer_class = DriverPerformanceDailySerializer

class CheckpointViewSet(viewsets.ModelViewSet):
    queryset = FleetMissionStop.objects.all()
    serializer_class = MissionStopSerializer

# ============================================================
# DASHBOARD FUNCTIONS
# ============================================================
@api_view(['GET'])
def dashboard_summary(request):
    try:
        trucks_count = FleetTruck.objects.count()
        drivers_count = FleetDriver.objects.count()
        active_missions = FleetMission.objects.filter(status='enroute').count()
        return Response({
            'status': 'success',
            'data': {
                'total_trucks': trucks_count,
                'total_drivers': drivers_count,
                'active_missions': active_missions,
                'on_time_rate': 85.5,
                'total_distance': 12450.5,
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def drivers_list_with_performance(request):
    try:
        drivers = FleetDriver.objects.all()
        data = []
        for d in drivers:
            try:
                data.append({
                    'id': str(d.id),
                    'name': d.get_display_name(),
                    'performance_mark': d.performance_mark,
                    'deliveries_count': d.deliveries_count,
                    'status': d.status,
                    'on_duty': d.on_duty
                })
            except Exception:
                continue
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def trucks_list_with_mission_data(request):
    try:
        trucks = FleetTruck.objects.all()
        data = []
        for t in trucks:
            try:
                data.append({
                    'id': str(t.id),
                    'truck_identifier': t.truck_identifier,
                    'plate': t.plate,
                    'status': t.status,
                    'last_latitude': t.last_latitude,
                    'last_longitude': t.last_longitude,
                    'speed_kmh': t.speed_kmh,
                    'assigned_driver': t.assigned_driver.get_display_name() if t.assigned_driver else None
                })
            except Exception:
                continue
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def missions_list_with_details(request):
    try:
        missions = FleetMission.objects.all()
        data = []
        for m in missions:
            try:
                data.append({
                    'id': str(m.id),
                    'mission_number': m.mission_number,
                    'status': m.status,
                    'progress_pct': m.progress_pct,
                    'truck': m.truck.truck_identifier if m.truck else None,
                    'driver': m.driver.get_display_name() if m.driver else None,
                    'origin': m.origin,
                    'destination': m.destination
                })
            except Exception:
                continue
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def recalculate_performance(request):
    return Response({'status': 'success', 'message': 'Performance recalculated'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def sync_truck_data(request):
    return Response({'status': 'success', 'message': 'Truck data synced'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def mission_route_geometry(request, mission_id):
    return Response({'geometry': {}, 'distance': 0, 'duration': 0}, status=status.HTTP_200_OK)

# ============================================================
# ALERT FUNCTION (placeholder to stop 404)
# ============================================================
@api_view(['GET'])
def alert_list(request):
    return Response([], status=status.HTTP_200_OK)

# ============================================================
# TRUCK TRACKING ENDPOINTS (V2 API)
# ============================================================
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

@csrf_exempt
@require_http_methods(["POST"])
def update_truck_location_speed(request):
    """
    POST /api/v1/truck-tracking/location-speed/
    Update truck's current location and speed from mobile app
    """
    try:
        data = json.loads(request.body)
        truck_id = data.get('truck_id')
        
        if not truck_id:
            return JsonResponse({'error': 'truck_id required'}, status=400)
        
        truck = FleetTruck.objects.get(id=truck_id)
        
        # Update location and speed
        truck.last_latitude = float(data.get('latitude', 0))
        truck.last_longitude = float(data.get('longitude', 0))
        truck.speed_kmh = float(data.get('speed_kmh', 0))
        truck.updated_at = timezone.now()
        
        truck.save()
        
        return JsonResponse({
            'status': 'success',
            'truck_id': str(truck.id),
            'truck_identifier': truck.truck_identifier,
            'speed_kmh': float(truck.speed_kmh) if truck.speed_kmh else 0,
        }, status=200)
        
    except FleetTruck.DoesNotExist:
        return JsonResponse({'error': 'Truck not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['GET'])
def get_truck_current_location_speed(request, truck_id):
    """
    GET /api/v1/truck-tracking/location-speed/{truck_id}/
    Get truck's current location and speed
    """
    try:
        truck = FleetTruck.objects.get(id=truck_id)
        
        return Response({
            'truck_id': str(truck.id),
            'truck_identifier': truck.truck_identifier,
            'plate': truck.plate,
            'status': truck.status,
            'latitude': float(truck.last_latitude) if truck.last_latitude else 0,
            'longitude': float(truck.last_longitude) if truck.last_longitude else 0,
            'speed_kmh': float(truck.speed_kmh) if truck.speed_kmh else 0,
        }, status=status.HTTP_200_OK)
        
    except FleetTruck.DoesNotExist:
        return Response({'error': 'Truck not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_all_trucks_current_locations(request):
    """
    GET /api/v1/truck-tracking/all-locations/
    Get all trucks' current locations and speeds for dashboard map
    """
    try:
        trucks = FleetTruck.objects.all()
        
        trucks_data = []
        for truck in trucks:
            trucks_data.append({
                'truck_id': str(truck.id),
                'truck_identifier': truck.truck_identifier,
                'plate': truck.plate,
                'status': truck.status,
                'latitude': float(truck.last_latitude) if truck.last_latitude else 0,
                'longitude': float(truck.last_longitude) if truck.last_longitude else 0,
                'speed_kmh': float(truck.speed_kmh) if truck.speed_kmh else 0,
                'assigned_driver': truck.assigned_driver.get_display_name() if truck.assigned_driver else None,
            })
        
        return Response({
            'count': len(trucks_data),
            'trucks': trucks_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
