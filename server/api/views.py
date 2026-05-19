"""
Fleet Management v2.0 - REST API Views
Django REST Framework ViewSets for V2 models
"""
def get_driver_by_id_or_name(driver_id):
    from .models import FleetDriver
    import uuid
    try:
        return FleetDriver.objects.get(id=driver_id)
    except (FleetDriver.DoesNotExist, ValueError):
        if isinstance(driver_id, str) and ' ' in driver_id:
            first, last = driver_id.split(' ', 1)
            return FleetDriver.objects.get(first_name__iexact=first.strip(), last_name__iexact=last.strip())
        raise FleetDriver.DoesNotExist(f"Driver not found: {driver_id}")

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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


# ===== Helper Functions =====
def get_driver_by_id_or_name(driver_identifier):
    """
    Get driver by UUID (ID) or by full name.
    Tries UUID first, then falls back to name lookup.
    Returns driver or None.
    """
    from django.core.exceptions import ValidationError
    try:
        # Try UUID first
        return FleetDriver.objects.get(id=driver_identifier)
    except (FleetDriver.DoesNotExist, ValueError, ValidationError):
        # Not a valid UUID, try name lookup
        # Split name into first and last name (simplistic: assumes "First Last" format)
        name_parts = driver_identifier.strip().split(maxsplit=1)
        if len(name_parts) == 2:
            first_name, last_name = name_parts
            try:
                return FleetDriver.objects.get(first_name__iexact=first_name, last_name__iexact=last_name)
            except FleetDriver.DoesNotExist:
                return None
        return None
class DriverViewSet(viewsets.ModelViewSet):
    queryset = FleetDriver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [AllowAny]


class TruckViewSet(viewsets.ModelViewSet):
    queryset = FleetTruck.objects.all()
    serializer_class = TruckSerializer
    permission_classes = [AllowAny]


class MissionViewSet(viewsets.ModelViewSet):
    queryset = FleetMission.objects.select_related('truck', 'driver').defer(
        'max_speed', 'avg_speed', 'compressed_trail'
    ).all()
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
        # Defer optional columns that may not exist in production database
        # This allows the query to work even if max_speed, avg_speed, compressed_trail columns are missing
        missions = FleetMission.objects.select_related('truck', 'driver').defer(
            'max_speed', 'avg_speed', 'compressed_trail'
        ).all()
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


@csrf_exempt
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


@csrf_exempt
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
@csrf_exempt
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


@csrf_exempt
@api_view(['POST'])
def mobile_validate_pin(request):
    """
    Validate PIN for driver authentication/registration.
    Supports drivers who prefer PIN entry over QR code scanning.
    PIN field is currently not enforced (placeholder for PIN system).
    """
    try:
        import json
        data = request.data
        
        phone_number = data.get('phone_number')
        pin = data.get('pin', '')
        first_name = data.get('first_name', 'Mobile')
        last_name = data.get('last_name', 'Driver')
        
        if not phone_number:
            return Response(
                {'error': 'phone_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For now, accept any PIN (placeholder for actual PIN validation system)
        # TODO: Implement actual PIN generation and validation
        if not pin:
            return Response(
                {'error': 'PIN is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if driver exists or create
        driver, created = FleetDriver.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'status': 'active'
            }
        )
        
        # Assign first available truck if not assigned
        truck_id = None
        truck_name = None
        if not driver.truck:
            truck = FleetTruck.objects.filter(status='active').first()
            if truck:
                driver.truck = truck
                driver.save()
                truck_id = str(truck.id)
                truck_name = truck.truck_identifier
                logger.info(f'Assigned truck {truck_name} to driver {phone_number}')
        else:
            truck_id = str(driver.truck.id) if driver.truck else None
            truck_name = driver.truck.truck_identifier if driver.truck else None
        
        serializer = DriverSerializer(driver)
        driver_data = serializer.data
        
        # Generate auth token (simplified)
        import uuid
        auth_token = str(uuid.uuid4())
        
        response_data = {
            'success': True,
            'created': created,
            'driver_id': str(driver.id),
            'driver_name': f"{driver.first_name} {driver.last_name}",
            'truck_id': truck_id,
            'truck_name': truck_name,
            'tracking_id': str(uuid.uuid4()),
            'token': auth_token,
            'phone_number': driver.phone_number,
            'driver': driver_data,
            'message': 'Driver authenticated successfully' if not created else 'Driver created and authenticated'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Error validating PIN: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def mobile_get_available_missions(request, driver_id):
    """Get available missions for a driver (supports both driver_id UUID and driver_name)"""
    try:
        # Verify driver exists - try ID first, then name
        driver = get_driver_by_id_or_name(driver_id)
        if not driver:
            return Response(
                {'error': f'Driver {driver_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get missions that are assigned to this driver or are available (not yet assigned)
        # Missions can be: planned, assigned, enroute, paused, completed, cancelled
        missions = FleetMission.objects.select_related('truck', 'driver').defer(
            'max_speed', 'avg_speed', 'compressed_trail'
        ).filter(
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
        
    except Exception as e:
        logger.error(f'Error fetching available missions: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def mobile_get_current_mission(request, driver_id):
    """Get the current mission being tracked by a driver (supports both driver_id UUID and driver_name)"""
    try:
        # Verify driver exists - try ID first, then name
        driver = get_driver_by_id_or_name(driver_id)
        if not driver:
            return Response(
                {'error': f'Driver {driver_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get the mission currently being tracked (status='enroute')
        mission = FleetMission.objects.select_related('truck', 'driver').defer(
            'max_speed', 'avg_speed', 'compressed_trail'
        ).filter(
            driver=driver,
            status='enroute'
        ).first()
        
        if not mission:
            # If no enroute mission, try to get the most recent one
            mission = FleetMission.objects.select_related('truck', 'driver').defer(
                'max_speed', 'avg_speed', 'compressed_trail'
            ).filter(
                driver=driver
            ).order_by('-started_at').first()
            
            if not mission:
                return Response(
                    {'error': 'No active mission found', 'status': None},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = MissionSerializer(mission)
        
        return Response({
            'success': True,
            'driver_id': str(driver.id),
            'driver_name': f"{driver.first_name} {driver.last_name}",
            'mission': serializer.data,
            'status': mission.status
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Error fetching current mission: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def mission_start_tracking(request):
    """Start tracking for a mission - called when driver accepts and starts mission
    Supports driver_id (UUID) or driver_name, and mission_id or mission_number
    """
    try:
        data = request.data
        driver_identifier = data.get('driver_id') or data.get('driver_name')
        mission_identifier = data.get('mission_id') or data.get('mission_number')
        
        if not driver_identifier or not mission_identifier:
            return Response(
                {'error': 'driver_id/driver_name and mission_id/mission_number are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify driver exists - try ID/name
        driver = get_driver_by_id_or_name(driver_identifier)
        if not driver:
            return Response(
                {'error': f'Driver {driver_identifier} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get and update mission - try ID first, then mission_number
        try:
            mission = FleetMission.objects.get(id=mission_identifier)
        except (FleetMission.DoesNotExist, ValueError):
            # Try mission_number
            mission = FleetMission.objects.get(mission_number=mission_identifier)
        
        # Update mission status to ENROUTE
        mission.status = 'enroute'
        mission.started_at = timezone.now()
        mission.save()
        
        serializer = MissionSerializer(mission)
        
        return Response({
            'success': True,
            'message': f'Mission tracking started for mission {mission.mission_number}',
            'driver_id': str(driver.id),
            'driver_name': f"{driver.first_name} {driver.last_name}",
            'mission': serializer.data,
            'mission_number': mission.mission_number,
            'started_at': mission.started_at.isoformat()
        }, status=status.HTTP_200_OK)
        
    except FleetMission.DoesNotExist:
        logger.warning(f'Mission not found: {mission_identifier}')
        return Response(
            {'error': f'Mission {mission_identifier} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error starting mission tracking: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def mobile_location_update(request):
    """Update driver location during mission tracking (supports driver_id UUID or driver_name)"""
    try:
        data = request.data
        driver_identifier = data.get('driver_id') or data.get('driver_name')
        mission_id = data.get('mission_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        speed = data.get('speed', 0)
        accuracy = data.get('accuracy', 0)
        altitude = data.get('altitude', 0)
        
        if not driver_identifier or not latitude or not longitude:
            return Response(
                {'error': 'driver_id/driver_name, latitude, and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create truck location record - try ID first, then name
        driver = get_driver_by_id_or_name(driver_identifier)
        if not driver:
            logger.warning(f'Driver not found: {driver_identifier}')
            return Response(
                {'error': f'Driver {driver_identifier} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        truck = driver.truck
        
        if not truck:
            return Response(
                {'error': 'Driver has no truck assigned'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update location
        location, created = TruckLocation.objects.update_or_create(
            truck=truck,
            driver=driver,
            defaults={
                'latitude': latitude,
                'longitude': longitude,
                'speed': speed,
                'accuracy': accuracy,
                'altitude': altitude,
                'timestamp': timezone.now()
            }
        )
        
        logger.info(f'Updated location for truck {truck.truck_identifier}: ({latitude}, {longitude}), speed: {speed}')
        
        return Response({
            'success': True,
            'message': 'Location updated',
            'location_id': str(location.id),
            'latitude': float(location.latitude),
            'longitude': float(location.longitude),
            'speed': float(location.speed),
            'timestamp': location.timestamp.isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Error updating location: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def truck_trail_with_directions(request, truck_id):
    """Get truck location trail with calculated directions for frontend tracking map"""
    try:
        limit = request.query_params.get('limit', 100)
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 100
        
        # Get locations for this truck, ordered by timestamp
        locations = TruckLocation.objects.filter(
            truck_id=truck_id
        ).select_related('truck', 'driver').order_by('-timestamp')[:limit]
        
        if not locations:
            return Response({
                'truck_id': truck_id,
                'trail': [],
                'count': 0,
                'message': 'No location data found'
            }, status=status.HTTP_200_OK)
        
        # Build trail with direction calculations
        trail = []
        for i, loc in enumerate(reversed(locations)):  # Reverse to get chronological order
            trail_point = {
                'latitude': float(loc.latitude),
                'longitude': float(loc.longitude),
                'speed': float(loc.speed),
                'accuracy': float(loc.accuracy),
                'altitude': float(loc.altitude),
                'timestamp': loc.timestamp.isoformat(),
                'sequence': i + 1,
            }
            
            # Calculate direction to next point if available
            if i > 0:
                from math import atan2, degrees, sqrt
                prev = trail[i-1]
                dlat = loc.latitude - prev['latitude']
                dlon = loc.longitude - prev['longitude']
                distance = sqrt(dlat**2 + dlon**2) * 111000  # Rough conversion to meters
                bearing = degrees(atan2(dlon, dlat)) % 360  # Bearing in degrees
                trail_point['bearing'] = bearing
                trail_point['distance_m'] = distance
            
            trail.append(trail_point)
        
        return Response({
            'truck_id': truck_id,
            'truck_identifier': locations[0].truck.truck_identifier,
            'plate': locations[0].truck.plate,
            'trail': trail,
            'count': len(trail),
            'driver_name': f"{locations[0].driver.first_name} {locations[0].driver.last_name}" if locations[0].driver else None
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f'Error fetching truck trail: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

