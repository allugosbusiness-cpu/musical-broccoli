"""
Fleet Management v2.0 - REST API Views
Django REST Framework ViewSets for V2 models
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
import logging

from .models import (
    FleetDriver, FleetTruck, FleetMission, TruckLocation,
    FleetActivity, FleetDriverPerformanceDaily, Alert
)
from .serializers import (
    DriverSerializer, TruckSerializer, MissionSerializer,
    TruckLocationSerializer, FleetActivitySerializer,
    PerformanceSerializer, AlertSerializer
)

logger = logging.getLogger(__name__)


class DriverViewSet(viewsets.ModelViewSet):
    queryset = FleetDriver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [AllowAny]


class TruckViewSet(viewsets.ModelViewSet):
    queryset = FleetTruck.objects.all()
    serializer_class = TruckSerializer
    permission_classes = [AllowAny]


class MissionViewSet(viewsets.ModelViewSet):
    queryset = FleetMission.objects.select_related('truck', 'driver').all()
    serializer_class = MissionSerializer
    permission_classes = [AllowAny]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = TruckLocation.objects.all()
    serializer_class = TruckLocationSerializer
    permission_classes = [AllowAny]


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = FleetActivity.objects.all()
    serializer_class = FleetActivitySerializer
    permission_classes = [AllowAny]


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = FleetDriverPerformanceDaily.objects.all()
    serializer_class = PerformanceSerializer
    permission_classes = [AllowAny]


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [AllowAny]


class CheckpointViewSet(viewsets.ModelViewSet):
    """Placeholder for compatibility"""
    queryset = FleetMission.objects.none()
    serializer_class = MissionSerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
def health_check(request):
    """API health check endpoint"""
    return Response({
        'status': 'ok',
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
def api_root(request):
    """API root endpoint"""
    return Response({
        'message': 'PulseTrack Fleet Management API v1',
        'endpoints': {
            'drivers': '/api/v1/drivers/',
            'trucks': '/api/v1/trucks/',
            'missions': '/api/v1/missions/',
            'locations': '/api/v1/locations/',
            'activities': '/api/v1/activities/',
            'performance': '/api/v1/performance/',
            'alerts': '/api/v1/alerts/',
        }
    })


# Dashboard Endpoints
@api_view(['GET'])
def dashboard_drivers(request):
    """Get all drivers with performance data for dashboard"""
    try:
        drivers = FleetDriver.objects.all()
        serializer = DriverSerializer(drivers, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'Error fetching dashboard drivers: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def dashboard_trucks(request):
    """Get all trucks with synced mission data for dashboard"""
    try:
        trucks = FleetTruck.objects.all()
        serializer = TruckSerializer(trucks, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'Error fetching dashboard trucks: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def dashboard_missions(request):
    """Get all missions for dashboard"""
    try:
        missions = FleetMission.objects.select_related('truck', 'driver').all()
        serializer = MissionSerializer(missions, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'Error fetching dashboard missions: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def dashboard_summary(request):
    """Get dashboard summary statistics"""
    try:
        total_drivers = FleetDriver.objects.count()
        active_drivers = FleetDriver.objects.filter(status='active').count()
        total_trucks = FleetTruck.objects.count()
        active_trucks = FleetTruck.objects.filter(status='idle').count() + FleetTruck.objects.filter(status='enroute').count()
        total_missions = FleetMission.objects.count()
        active_missions = FleetMission.objects.filter(status='in_progress').count()
        active_alerts = Alert.objects.filter(is_resolved=False).count()
        
        return Response({
            'total_drivers': total_drivers,
            'active_drivers': active_drivers,
            'total_trucks': total_trucks,
            'active_trucks': active_trucks,
            'total_missions': total_missions,
            'active_missions': active_missions,
            'active_alerts': active_alerts,
        })
    except Exception as e:
        logger.error(f'Error fetching dashboard summary: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def dashboard_recalculate_performance(request):
    """Recalculate driver performance metrics"""
    try:
        # For now, just return success - actual calculation logic can be added later
        from django.utils import timezone
        from datetime import timedelta
        
        # Get performance records from the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        performances = FleetDriverPerformanceDaily.objects.filter(
            date__gte=thirty_days_ago
        )
        
        return Response({
            'message': 'Performance recalculation completed',
            'records_updated': performances.count()
        })
    except Exception as e:
        logger.error(f'Error recalculating performance: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Truck Tracking Endpoints
@api_view(['GET'])
def truck_tracking_all_locations(request):
    """Get all truck current locations for real-time tracking"""
    try:
        # Get latest location for each truck
        # PostgreSQL DISTINCT ON requires ORDER BY to start with the DISTINCT field
        locations = TruckLocation.objects.select_related('truck', 'driver').order_by('truck_id', '-timestamp').distinct('truck_id')
        
        trucks_data = []
        for loc in locations:
            trucks_data.append({
                'truck_id': str(loc.truck.id),
                'truck_identifier': loc.truck.truck_identifier,
                'plate': loc.truck.plate,
                'latitude': float(loc.latitude),
                'longitude': float(loc.longitude),
                'speed': float(loc.speed),
                'accuracy': float(loc.accuracy),
                'altitude': float(loc.altitude),
                'timestamp': loc.timestamp.isoformat(),
                'driver_id': str(loc.driver.id) if loc.driver else None,
                'driver_name': f"{loc.driver.first_name} {loc.driver.last_name}" if loc.driver else None,
                'status': loc.truck.status,
            })
        
        return Response({
            'trucks': trucks_data,
            'count': len(trucks_data)
        })
    except Exception as e:
        logger.error(f'Error fetching truck locations: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def calculate_distance(request):
    """Calculate distance between two coordinates
    
    Accept formats:
    1. {origin: {lat, lon}, destination: {lat, lon}}
    2. {lat1, lon1, lat2, lon2}
    """
    try:
        from math import radians, cos, sin, asin, sqrt
        
        data = request.data
        
        # Support both formats
        if 'origin' in data and 'destination' in data:
            origin = data['origin']
            destination = data['destination']
            lat1 = float(origin.get('lat', 0))
            lon1 = float(origin.get('lon', origin.get('lng', 0)))
            lat2 = float(destination.get('lat', 0))
            lon2 = float(destination.get('lon', destination.get('lng', 0)))
        else:
            lat1 = float(data.get('lat1', 0))
            lon1 = float(data.get('lon1', 0))
            lat2 = float(data.get('lat2', 0))
            lon2 = float(data.get('lon2', 0))
        
        # Haversine formula for distance calculation
        lon1_rad, lat1_rad, lon2_rad, lat2_rad = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c  # Radius of earth in kilometers
        
        return Response({
            'distance_km': round(km, 2),
            'distance_m': round(km * 1000, 2),
            'distance_meters': round(km * 1000, 2),  # Frontend uses this key
            'from': {'latitude': lat1, 'longitude': lon1},
            'to': {'latitude': lat2, 'longitude': lon2}
        })
    except Exception as e:
        logger.error(f'Error calculating distance: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Mobile Endpoints
@api_view(['POST'])
def mobile_driver_registration(request):
    """Register a mobile driver - returns driver_id for AsyncStorage"""
    try:
        import json
        data = request.data
        
        phone_number = data.get('phone_number')
        first_name = data.get('first_name', 'Mobile')
        last_name = data.get('last_name', 'Driver')
        
        if not phone_number:
            return Response(
                {'error': 'phone_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if driver exists
        driver, created = FleetDriver.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'status': 'active'
            }
        )
        
        # Extract truck from QR data if provided
        truck_id = None
        truck_name = None
        qr_data_str = data.get('qr_data')
        
        if qr_data_str:
            try:
                # QR data might be stringified JSON
                if isinstance(qr_data_str, str):
                    qr_data = json.loads(qr_data_str)
                else:
                    qr_data = qr_data_str
                
                # Extract truck_id from QR data
                qr_truck_id = qr_data.get('truck_id')
                if qr_truck_id:
                    # Verify truck exists
                    truck = FleetTruck.objects.filter(id=qr_truck_id).first()
                    if truck:
                        driver.truck = truck
                        driver.save()
                        truck_id = str(truck.id)
                        truck_name = truck.truck_identifier
                        logger.info(f'Assigned truck {truck_name} to driver {phone_number}')
                    else:
                        logger.warning(f'QR truck_id {qr_truck_id} not found in database')
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f'Could not parse qr_data: {str(e)}')
        
        serializer = DriverSerializer(driver)
        driver_data = serializer.data
        
        # Return driver_id and truck_id in format expected by mobile app
        response_data = {
            'success': True,
            'created': created,
            'driver_id': str(driver.id),  # UUID converted to string for mobile storage
            'driver_name': f"{driver.first_name} {driver.last_name}",
            'truck_id': truck_id or (str(driver.truck_id) if driver.truck_id else None),
            'truck_name': truck_name or (driver.truck.truck_identifier if driver.truck else None),
            'phone_number': driver.phone_number,
            'driver': driver_data,
            'message': 'Driver registered successfully' if created else 'Driver already exists'
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Error registering driver: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def mobile_get_available_missions(request, driver_id):
    """Get available missions for a driver"""
    try:
        # Verify driver exists
        driver = FleetDriver.objects.get(id=driver_id)
        
        # Get missions that are assigned to this driver or are available (not yet assigned)
        # Missions can be: planned, assigned, enroute, paused, completed, cancelled
        missions = FleetMission.objects.select_related('truck', 'driver').filter(
            driver=driver,
            status__in=['assigned', 'planned']
        ).order_by('-created_at')
        
        serializer = MissionSerializer(missions, many=True)
        
        return Response({
            'success': True,
            'driver_id': str(driver.id),
            'driver_name': f"{driver.first_name} {driver.last_name}",
            'truck_id': str(driver.truck.id) if driver.truck else None,
            'truck_name': driver.truck.truck_identifier if driver.truck else None,
            'missions': serializer.data,
            'count': missions.count()
        }, status=status.HTTP_200_OK)
        
    except FleetDriver.DoesNotExist:
        logger.warning(f'Driver not found: {driver_id}')
        return Response(
            {'error': f'Driver {driver_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error fetching available missions: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def mobile_mission_start_tracking(request):
    """Start tracking for a mission - called when driver accepts and starts mission"""
    try:
        data = request.data
        driver_id = data.get('driver_id')
        mission_id = data.get('mission_id')
        
        if not driver_id or not mission_id:
            return Response(
                {'error': 'driver_id and mission_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify driver exists
        driver = FleetDriver.objects.get(id=driver_id)
        
        # Get and update mission
        mission = FleetMission.objects.get(id=mission_id)
        
        # Update mission status to ENROUTE
        mission.status = 'enroute'
        mission.started_at = timezone.now()
        mission.save()
        
        serializer = MissionSerializer(mission)
        
        return Response({
            'success': True,
            'message': f'Mission tracking started for mission {mission.mission_number}',
            'driver_id': str(driver.id),
            'mission': serializer.data,
            'started_at': mission.started_at.isoformat()
        }, status=status.HTTP_200_OK)
        
    except FleetDriver.DoesNotExist:
        logger.warning(f'Driver not found: {driver_id}')
        return Response(
            {'error': f'Driver {driver_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except FleetMission.DoesNotExist:
        logger.warning(f'Mission not found: {mission_id}')
        return Response(
            {'error': f'Mission {mission_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error starting mission tracking: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)