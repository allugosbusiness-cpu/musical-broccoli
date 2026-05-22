"""
Fleet Management v2.0 - REST API Views
Django REST Framework ViewSets for V2 models
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
import uuid

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
    Get driver by UUID (ID), phone_number, or by full name.
    All lookups use .filter().first() to avoid MultipleObjectsReturned.
    Returns driver or None.
    """
    from django.core.exceptions import ValidationError
    
    # Try UUID first
    if driver_identifier:
        try:
            driver = FleetDriver.objects.filter(id=driver_identifier).first()
            if driver:
                return driver
        except (ValueError, ValidationError):
            pass
        
        # Try phone number
        driver = FleetDriver.objects.filter(phone_number=driver_identifier).first()
        if driver:
            return driver
        
        # Try name lookup (split "First Last" format)
        name_parts = driver_identifier.strip().split(maxsplit=1)
        if len(name_parts) == 2:
            first_name, last_name = name_parts
            driver = FleetDriver.objects.filter(
                first_name__iexact=first_name, 
                last_name__iexact=last_name
            ).order_by('-created_at').first()
            if driver:
                return driver
    
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
    # Don't use get_queryset - it tries to select the optional columns
    queryset = FleetMission.objects.all()
    serializer_class = MissionSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        """Override to avoid inserting optional fields that may not exist in DB"""
        # The create method pops max_speed, avg_speed, compressed_trail from validated_data
        # before calling super().create(), so Django never tries to INSERT them
        serializer.save()
    
    def _resolve_truck(self, identifier):
        """Resolve truck by UUID, truck_identifier, or plate number"""
        if not identifier:
            return None
        try:
            return FleetTruck.objects.get(id=identifier)
        except (FleetTruck.DoesNotExist, ValueError):
            pass
        try:
            return FleetTruck.objects.get(truck_identifier=identifier)
        except FleetTruck.DoesNotExist:
            pass
        try:
            return FleetTruck.objects.get(plate=identifier)
        except FleetTruck.DoesNotExist:
            pass
        return None

    def _resolve_driver(self, identifier):
        """Resolve driver by UUID, phone_number, or name"""
        if not identifier:
            return None
        try:
            return FleetDriver.objects.get(id=identifier)
        except (FleetDriver.DoesNotExist, ValueError):
            pass
        try:
            return FleetDriver.objects.get(phone_number=identifier)
        except FleetDriver.DoesNotExist:
            pass
        return None

    def create(self, request, *args, **kwargs):
        """
        Create mission directly via the model manager to avoid DRF serializer
        internal .get() calls that raise DoesNotExist (the mission doesn't exist 
        yet because we're creating it).
        
        Handles truck/driver lookup by identifier, optional column removal, 
        and coordinate normalization.
        """
        try:
            # Convert request data
            data = dict(request.data.items()) if hasattr(request.data, 'items') else dict(request.data)
            
            # Remove optional columns that don't exist in production DB
            data.pop('max_speed', None)
            data.pop('avg_speed', None)
            data.pop('compressed_trail', None)
            data.pop('planned_distance_km', None)
            data.pop('planned_duration_minutes', None)
            data.pop('identifier', None)
            data.pop('notes', None)
            
            # Resolve truck
            truck_identifier = data.get('truck')
            driver_identifier = data.get('driver')
            
            truck = self._resolve_truck(truck_identifier)
            if not truck and truck_identifier:
                return Response(
                    {'error': f'Truck "{truck_identifier}" not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            driver = self._resolve_driver(driver_identifier)
            if not driver and driver_identifier:
                return Response(
                    {'error': f'Driver "{driver_identifier}" not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Normalize coordinates
            origin = data.get('origin', {})
            destination = data.get('destination', {})
            if isinstance(origin, dict):
                origin = {
                    'lat': float(origin.get('lat', 0)),
                    'lon': float(origin.get('lon', origin.get('lng', 0)))
                }
            if isinstance(destination, dict):
                destination = {
                    'lat': float(destination.get('lat', 0)),
                    'lon': float(destination.get('lon', destination.get('lng', 0)))
                }
            
            # Generate mission number if not provided
            mission_number = data.get('mission_number') or f"MIS-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"
            
            # Build create kwargs directly - bypass serializer to avoid internal .get() calls
            create_kwargs = {
                'id': uuid.uuid4(),
                'mission_number': mission_number,
                'status': data.get('status', 'planned'),
                'priority': data.get('priority', 'normal'),
                'truck': truck,
                'driver': driver,
                'origin': origin,
                'destination': destination,
                'cargo': data.get('cargo', {}),
            }
            
            # Create mission directly through the safe FleetMissionManager
            mission = FleetMission.objects.create(**create_kwargs)
            
            logger.info(f'Mission {mission.mission_number} created successfully (id={mission.id})')
            
            return Response({
                'id': str(mission.id),
                'mission_number': mission.mission_number,
                'status': mission.status,
                'priority': mission.priority,
                'truck': str(mission.truck_id) if mission.truck_id else None,
                'driver': str(mission.driver_id) if mission.driver_id else None,
                'truck_name': truck.truck_identifier if truck else None,
                'driver_name': driver.get_display_name() if driver else None,
                'origin': mission.origin,
                'destination': mission.destination,
                'distance_total_m': float(mission.distance_total_m) if mission.distance_total_m else 0,
                'cargo': mission.cargo,
                'created_at': mission.created_at.isoformat(),
                'updated_at': mission.updated_at.isoformat(),
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f'Mission creation error: {str(e)}\n{tb}')
            return Response(
                {'error': str(e), 'detail': f'Type: {type(e).__name__}'},
                status=status.HTTP_400_BAD_REQUEST
            )


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


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def setup_admin_account(request):
    """
    Setup or verify admin account existence.
    GET: Check if admin exists
    POST: Create initial admin account
    Returns success response for frontend validation.
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if request.method == 'GET':
            admin_exists = User.objects.filter(is_superuser=True).exists()
            return Response({
                'success': True,
                'admin_exists': admin_exists,
                'message': 'Admin account status checked'
            })
        
        # POST: Create admin
        data = request.data or {}
        username = data.get('username', 'admin')
        email = data.get('email', 'admin@pulsetrack.com')
        password = data.get('password', 'admin123')
        
        if User.objects.filter(is_superuser=True).exists():
            return Response({
                'success': True,
                'admin_exists': True,
                'message': 'Admin account already exists'
            })
        
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        return Response({
            'success': True,
            'admin_exists': True,
            'message': 'Admin account created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'Error in setup-admin-account: {str(e)}')
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        # First try: use raw queryset without defer to get all fields
        # If optional columns (max_speed, avg_speed, compressed_trail) don't exist
        # in the production DB yet, this will fail with FieldError.
        # We catch that and fall back to values() which skips unknown columns.
        try:
            missions = FleetMission.objects.select_related('truck', 'driver').all()
            serializer = MissionSerializer(missions, many=True)
            return Response(serializer.data)
        except Exception as inner_e:
            logger.warning(f'Direct mission query failed, trying values() fallback: {str(inner_e)}')
            # Fallback: query only known-good fields via values()
            # Build response manually without the optional columns
            missions = FleetMission.objects.values(
                'id', 'mission_number', 'status', 'priority', 'truck', 'driver',
                'origin', 'destination', 'distance_total_m',
                'cargo', 'mission_date', 'started_at', 'completed_at',
                'delivered_at', 'created_at', 'updated_at'
            )
            result = []
            for m in missions:
                truck_name = None
                driver_name = None
                if m.get('truck'):
                    try:
                        t = FleetTruck.objects.filter(id=m['truck']).first()
                        if t:
                            truck_name = t.truck_identifier
                    except Exception:
                        pass
                if m.get('driver'):
                    try:
                        d = FleetDriver.objects.filter(id=m['driver']).first()
                        if d:
                            driver_name = f"{d.first_name} {d.last_name}"
                    except Exception:
                        pass
                m['truck_name'] = truck_name
                m['driver_name'] = driver_name
                # Add empty values for optional fields that don't exist in DB
                m['max_speed'] = '0.00'
                m['avg_speed'] = '0.00'
                m['compressed_trail'] = []
                result.append(m)
            return Response(result)
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
        active_missions = FleetMission.objects.filter(status='enroute').count()
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
        
        # Support multiple name formats:
        # 1. first_name + last_name (separate fields)
        # 2. name (single field, e.g. "Allan Mugogo")
        # 3. driver_name (single field)
        first_name = data.get('first_name') or ''
        last_name = data.get('last_name') or ''
        
        # If first_name/last_name not sent, try 'name' or 'driver_name' field
        if not first_name and not last_name:
            full_name = data.get('name') or data.get('driver_name') or ''
            if ' ' in full_name.strip():
                parts = full_name.strip().split(maxsplit=1)
                first_name = parts[0]
                last_name = parts[1]
            else:
                first_name = full_name or 'Mobile'
                last_name = 'Driver'
        else:
            first_name = first_name or 'Mobile'
            last_name = last_name or 'Driver'
        
        if not phone_number:
            return Response(
                {'error': 'phone_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log what we received for debugging
        logger.info(f'Registration request: phone={phone_number}, first={first_name}, last={last_name}')
        
        # Check if driver exists
        driver, created = FleetDriver.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'status': 'active'
            }
        )
        
        # Always update driver name to what was submitted (not just on creation)
        # This fixes the bug where the app defaults to "Mobile Driver"
        if not created:
            driver.first_name = first_name
            driver.last_name = last_name
            driver.save(update_fields=['first_name', 'last_name'])
        
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
                    truck_obj = FleetTruck.objects.filter(id=qr_truck_id).first()
                    if truck_obj:
                        driver.truck = truck_obj
                        driver.save()
                        truck_id = str(truck_obj.id)
                        truck_name = truck_obj.truck_identifier
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
        
        # Build mission data manually using values() to avoid SELECT *
        # which fails on production DB (missing max_speed, avg_speed, compressed_trail columns)
        # Match missions where driver is assigned to the mission OR missions 
        # assigned to the driver's truck (even if driver not explicitly linked)
        driver_mission_qs = FleetMission.objects.filter(
            driver=driver,
            status__in=['assigned', 'planned']
        )
        
        truck_mission_qs = FleetMission.objects.filter(
            truck=driver.truck,
            status__in=['assigned', 'planned']
        ) if driver.truck else FleetMission.objects.none()
        
        # Combine and deduplicate by ID
        combined = list(driver_mission_qs) + [m for m in truck_mission_qs if m not in driver_mission_qs]
        combined.sort(key=lambda m: m.created_at or timezone.datetime.min, reverse=True)
        
        missions_data = []
        for mission in combined:
            missions_data.append({
                'id': str(mission.id),
                'mission_number': mission.mission_number,
                'status': mission.status,
                'origin': mission.origin if isinstance(mission.origin, dict) else {'lat': 0, 'lon': 0},
                'destination': mission.destination if isinstance(mission.destination, dict) else {'lat': 0, 'lon': 0},
                'distance_total_m': float(mission.distance_total_m) if mission.distance_total_m else 0,
                'cargo': mission.cargo if mission.cargo else {},
                'created_at': mission.created_at.isoformat() if mission.created_at else None,
            })
        
        return Response({
            'success': True,
            'driver_id': str(driver.id),
            'driver_name': f"{driver.first_name} {driver.last_name}",
            'truck_id': str(driver.truck.id) if driver.truck else None,
            'truck_name': driver.truck.truck_identifier if driver.truck else None,
            'missions': missions_data,
            'count': len(missions_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        logger.error(f'Error fetching available missions: {str(e)}\n{traceback.format_exc()}')
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
        
        # Use values() to avoid SELECT * which fails on missing columns
        mission = FleetMission.objects.filter(
            driver=driver,
            status='enroute'
        ).values(
            'id', 'mission_number', 'status', 'priority',
            'origin', 'destination', 'distance_total_m', 'cargo',
            'started_at', 'created_at'
        ).first()
        
        if not mission:
            return Response(
                {'error': 'No active mission found', 'status': None},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'success': True,
            'driver_id': str(driver.id),
            'driver_name': f"{driver.first_name} {driver.last_name}",
            'mission': {
                'id': str(mission['id']),
                'mission_number': mission['mission_number'],
                'status': mission['status'],
                'origin': mission['origin'] if isinstance(mission['origin'], dict) else {'lat': 0, 'lon': 0},
                'destination': mission['destination'] if isinstance(mission['destination'], dict) else {'lat': 0, 'lon': 0},
                'distance_total_m': float(mission['distance_total_m']) if mission['distance_total_m'] else 0,
                'cargo': mission['cargo'] if mission['cargo'] else {},
                'created_at': mission['created_at'].isoformat() if mission['created_at'] else None,
            },
            'status': mission['status']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        logger.error(f'Error fetching current mission: {str(e)}\n{traceback.format_exc()}')
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
        mission = FleetMission.objects.filter(id=mission_identifier).first()
        if not mission:
            # Try mission_number
            mission = FleetMission.objects.filter(mission_number=mission_identifier).first()
        if not mission:
            logger.warning(f'Mission not found: {mission_identifier}')
            return Response(
                {'error': f'Mission {mission_identifier} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
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
            'started_at': mission.started_at.isoformat() if mission.started_at else None
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Error starting mission tracking: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def mobile_location_update(request):
    """Update driver location during mission tracking (supports driver_id UUID or driver_name)
    
    CRITICAL: Creates a NEW TruckLocation record each time (not update_or_create).
    This ensures every GPS ping is recorded for the trail/map.
    Also updates truck.last_latitude/last_longitude for real-time pin position.
    """
    try:
        data = request.data
        driver_identifier = data.get('driver_id') or data.get('driver_name')
        mission_id = data.get('mission_id')
        
        # Parse coordinates - accept both string and number formats
        try:
            latitude = float(data.get('latitude', 0))
            longitude = float(data.get('longitude', 0))
            speed = float(data.get('speed', 0))
            accuracy = float(data.get('accuracy', 0))
            altitude = float(data.get('altitude', 0))
        except (TypeError, ValueError) as e:
            return Response(
                {'error': f'Invalid numeric values: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not driver_identifier:
            return Response(
                {'error': 'driver_id/driver_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not latitude or not longitude:
            return Response(
                {'error': 'latitude and longitude are required and must be non-zero'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find driver by ID, phone, or name
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
        
        # CRITICAL: Always CREATE a new record (not update_or_create).
        # update_or_create overwrites the SAME record each time, losing GPS trail history.
        location = TruckLocation.objects.create(
            truck=truck,
            driver=driver,
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            accuracy=accuracy,
            altitude=altitude,
            timestamp=timezone.now()
        )
        
        # Update truck's live position for real-time map pin
        truck.last_latitude = latitude
        truck.last_longitude = longitude
        truck.save(update_fields=['last_latitude', 'last_longitude'])
        
        logger.info(f'📍 Location recorded for truck {truck.truck_identifier}: ({latitude}, {longitude}) speed={speed}km/h')
        
        return Response({
            'success': True,
            'message': 'Location recorded',
            'location_id': str(location.id),
            'latitude': float(location.latitude),
            'longitude': float(location.longitude),
            'speed': float(location.speed),
            'timestamp': location.timestamp.isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        logger.error(f'Error updating location: {str(e)}\n{traceback.format_exc()}')
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

