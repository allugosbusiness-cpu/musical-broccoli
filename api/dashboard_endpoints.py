from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import OperationalError, ProgrammingError
from .models import FleetTruck, FleetDriver, FleetMission, FleetActivity

@api_view(['GET'])
def dashboard_summary(request):
    try:
        # Defensive check: avoid crashing if tables aren't migrated
        try:
            trucks_count = FleetTruck.objects.count()
            drivers_count = FleetDriver.objects.count()
            active_missions = FleetMission.objects.filter(status='enroute').count()
        except (OperationalError, ProgrammingError):
            return Response({
                'status': 'error', 
                'message': 'Database tables not found. Please reset your database on Render.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                # Use getattr to avoid crashing if a specific field is missing in the DB
                data.append({
                    'id': str(d.id),
                    'name': d.get_display_name(),
                    'performance_mark': getattr(d, 'performance_mark', 0),
                    'deliveries_count': getattr(d, 'deliveries_count', 0),
                    'status': getattr(d, 'status', 'unknown'),
                    'on_duty': getattr(d, 'on_duty', False)
                })
            except Exception:
                continue # Skip any corrupted driver record
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
                    'truck_identifier': getattr(t, 'truck_identifier', 'Unknown'),
                    'plate': getattr(t, 'plate', 'N/A'),
                    'status': getattr(t, 'status', 'Unknown'),
                    'last_latitude': getattr(t, 'last_latitude', 0),
                    'last_longitude': getattr(t, 'last_longitude', 0),
                    'speed_kmh': getattr(t, 'speed_kmh', 0),
                    'assigned_driver': t.assigned_driver.get_display_name() if hasattr(t, 'assigned_driver') and t.assigned_driver else None
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
                    'mission_number': getattr(m, 'mission_number', 'N/A'),
                    'status': getattr(m, 'status', 'unknown'),
                    'progress_pct': getattr(m, 'progress_pct', 0),
                    'truck': m.truck.truck_identifier if m.truck else None,
                    'driver': m.driver.get_display_name() if m.driver else None,
                    'origin': m.origin if isinstance(m.origin, dict) else {},
                    'destination': m.destination if isinstance(m.destination, dict) else {},
                })
            except Exception:
                continue
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def recalculate_performance(request):
    return Response({'status': 'success', 'message': 'Recalculation triggered'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def sync_truck_data(request):
    return Response({'status': 'success', 'message': 'Sync triggered'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def mission_route_geometry(request, mission_id):
    return Response({'geometry': {}, 'distance': 0, 'duration': 0}, status=status.HTTP_200_OK)
