# server/api/mobile_endpoints.py
"""
Mobile app API endpoints for real-time driver tracking
Handles location updates, alerts, and driver registration via QR codes
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
import json
import qrcode
import uuid
from io import BytesIO
import base64
from datetime import datetime, timedelta

from .models_v2 import FleetDriver, FleetTruck, FleetMission, TruckLocation
from .models import Alert
from .serializers import TruckSerializer, AlertSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_health_check(request):
    """
    ✅ Health check endpoint for mobile app
    Diagnostic endpoint to verify backend is responding with per-table error isolation
    """
    diagnostics = {
        'status': 'unknown',
        'timestamp': timezone.now().isoformat(),
        'database': {},
        'message': '',
    }
    
    try:
        # Test each database table individually to isolate errors
        try:
            driver_count = FleetDriver.objects.count()
            diagnostics['database']['drivers'] = {
                'status': 'ok',
                'count': driver_count
            }
        except Exception as db_error:
            diagnostics['database']['drivers'] = {
                'status': 'error',
                'error': str(db_error)
            }
        
        try:
            truck_count = FleetTruck.objects.count()
            diagnostics['database']['trucks'] = {
                'status': 'ok',
                'count': truck_count
            }
        except Exception as db_error:
            diagnostics['database']['trucks'] = {
                'status': 'error',
                'error': str(db_error)
            }
        
        try:
            mission_count = FleetMission.objects.count()
            diagnostics['database']['missions'] = {
                'status': 'ok',
                'count': mission_count
            }
        except Exception as db_error:
            diagnostics['database']['missions'] = {
                'status': 'error',
                'error': str(db_error)
            }
        
        # Determine overall status based on per-table results
        db_errors = [v for v in diagnostics['database'].values() if v.get('status') == 'error']
        if db_errors:
            diagnostics['status'] = 'unhealthy'
            diagnostics['message'] = f'❌ {len(db_errors)} database tables unreachable'
            return Response(diagnostics, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            diagnostics['status'] = 'healthy'
            diagnostics['message'] = '✅ Backend is operational'
            return Response(diagnostics, status=status.HTTP_200_OK)
            
    except Exception as e:
        import traceback
        diagnostics['status'] = 'error'
        diagnostics['message'] = '❌ Unexpected backend error'
        diagnostics['error'] = str(e)
        diagnostics['traceback'] = traceback.format_exc()
        return Response(diagnostics, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def mobile_driver_registration(request):
    """
    Register driver by scanning QR code on truck
    QR contains truck UUID, driver provides phone number
    """
    try:
        qr_data = request.data.get('qr_data', '')
        phone_number = request.data.get('phone_number', '')

        if not qr_data or not phone_number:
            return Response(
                {'error': 'QR data and phone number required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse QR data
        try:
            qr_info = json.loads(qr_data)
            truck_id = qr_info.get('truck_id')
        except json.JSONDecodeError:
            truck_id = qr_data  # Assume it's just the truck UUID

        # Get truck
        try:
            truck = FleetTruck.objects.get(id=truck_id)
        except FleetTruck.DoesNotExist:
            return Response(
                {'error': 'Truck not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get or create driver
        driver, created = FleetDriver.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'first_name': 'Driver',
                'last_name': phone_number[-4:],
                'email': f'driver_{phone_number}@fleet.local',
                'fleet_id': truck.fleet_id,
            }
        )

        # Update driver to active and assign truck
        driver.truck = truck
        driver.is_active = True
        driver.save()

        # Generate unique auth token and tracking session ID
        import uuid
        auth_token = str(uuid.uuid4())
        tracking_id = str(uuid.uuid4())
        
        # Store tracking session in cache or database
        from django.core.cache import cache
        cache.set(f'driver_tracking_{driver.id}', {
            'tracking_id': tracking_id,
            'driver_id': str(driver.id),
            'truck_id': str(truck.id),
            'started_at': datetime.now().isoformat(),
            'gps_enabled': True
        }, timeout=None)  # Keep indefinitely until explicitly cleared
        
        return Response({
            'driver_id': str(driver.id),
            'truck_id': str(truck.id),
            'tracking_id': tracking_id,
            'token': auth_token,
            'driver_name': f'{driver.first_name} {driver.last_name}',
            'truck_name': truck.truck_identifier,
            'phone_number': phone_number,
            'first_name': driver.first_name,
            'last_name': driver.last_name,
            'gps_tracking_enabled': True,
            'success': True
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def mobile_location_update(request):
    """
    Receive location update from mobile app
    Called every 2 minutes with driver position, speed, accuracy
    """
    try:
        driver_id = request.data.get('driver_id')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        speed = request.data.get('speed', 0)  # km/h
        accuracy = request.data.get('accuracy', 0)
        altitude = request.data.get('altitude', 0)
        timestamp = request.data.get('timestamp', int(datetime.now().timestamp() * 1000))

        # Validate required fields
        if not driver_id or latitude is None or longitude is None:
            return Response(
                {'error': 'driver_id, latitude, longitude required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get driver
        try:
            driver = FleetDriver.objects.get(id=driver_id)
        except FleetDriver.DoesNotExist:
            return Response(
                {'error': 'Driver not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update driver location
        driver.latitude = latitude
        driver.longitude = longitude
        driver.current_speed = speed
        driver.updated_at = timezone.now()
        driver.save()

        # Update truck's location as well (critical for map display!)
        if driver.truck:
            driver.truck.last_latitude = latitude
            driver.truck.last_longitude = longitude
            driver.truck.speed_kmh = speed
            driver.truck.updated_at = timezone.now()
            # Update mission's current location if active mission exists
            active_mission = FleetMission.objects.filter(
                truck=driver.truck,
                status='enroute'
            ).first()
            if active_mission:
                active_mission.current_location = {
                    'lat': latitude,
                    'lon': longitude
                }
                active_mission.speed_kmh = speed
                active_mission.save(update_fields=['current_location', 'speed_kmh', 'updated_at'])
            driver.truck.save()

        # Store location history
        TruckLocation.objects.create(
            truck=driver.truck,
            driver=driver,
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            accuracy=accuracy,
            altitude=altitude,
            timestamp=timezone.datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        )

        # Check for overspeeding alert
        if speed > 120:  # 120 km/h threshold
            Alert.objects.create(
                driver=driver,
                truck=driver.truck,
                alert_type='overspeeding',
                message=f'Overspeeding: {speed} km/h',
                latitude=latitude,
                longitude=longitude,
                speed=speed
            )

        return Response({
            'success': True,
            'message': 'Location updated',
            'driver_id': str(driver.id),
            'truck_id': str(driver.truck.id) if driver.truck else None
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def mobile_alert(request):
    """
    Receive alert from mobile app
    Alert types: overspeeding, route_deviation, wrong_location, driver_initiated, mechanical_issue
    """
    try:
        driver_id = request.data.get('driver_id')
        alert_type = request.data.get('alert_type')
        message = request.data.get('message')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        speed = request.data.get('speed', 0)

        # Validate
        if not all([driver_id, alert_type, message, latitude is not None, longitude is not None]):
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get driver
        try:
            driver = FleetDriver.objects.get(id=driver_id)
        except FleetDriver.DoesNotExist:
            return Response(
                {'error': 'Driver not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create alert
        alert = Alert.objects.create(
            driver=driver,
            truck=driver.truck,
            alert_type=alert_type,
            message=message,
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            severity='high' if alert_type in ['overspeeding', 'route_deviation'] else 'medium'
        )

        # TODO: Trigger notification to admin dashboard
        # TODO: Send notification to dispatcher

        return Response({
            'success': True,
            'alert_id': str(alert.id),
            'message': 'Alert recorded'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def mobile_driver_profile(request, driver_id):
    """
    Get driver profile with performance points and current mission
    """
    try:
        driver = FleetDriver.objects.get(id=driver_id)

        # Get current mission
        current_mission = FleetMission.objects.filter(
            truck=driver.truck,
            status='in_progress'
        ).first()

        return Response({
            'id': str(driver.id),
            'name': driver.name,
            'phone': driver.phone_number,
            'email': driver.email,
            'performance_points': driver.performance_mark,
            'current_speed': driver.current_speed or 0,
            'latitude': driver.latitude,
            'longitude': driver.longitude,
            'truck_id': str(driver.truck.id) if driver.truck else None,
            'truck_name': driver.truck.truck_name if driver.truck else None,
            'current_mission': {
                'id': str(current_mission.id),
                'mission_number': current_mission.mission_number,
                'status': current_mission.status,
                'distance_total_m': current_mission.distance_total_m,
                'progress_pct': current_mission.progress_pct,
                'origin': {'lat': float(current_mission.origin_latitude), 'lon': float(current_mission.origin_longitude)},
                'destination': {'lat': float(current_mission.destination_latitude), 'lon': float(current_mission.destination_longitude)},
            } if current_mission else None,
        }, status=status.HTTP_200_OK)

    except FleetDriver.DoesNotExist:
        return Response(
            {'error': 'Driver not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_driver_current_mission(request, driver_id):
    """
    Get current mission for driver with robust error handling
    Returns the active (enroute) mission with proper coordinate handling
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # ✅ Get driver with defensive checks
        driver = FleetDriver.objects.get(id=driver_id)
        
        if not driver.truck:
            logger.warning(f"Driver {driver_id} has no truck assigned")
            return Response({
                'error': 'Driver has no truck assigned',
                'id': None,
                'mission_number': None,
                'status': None,
            }, status=status.HTTP_200_OK)

        # ✅ Get active mission - use Q to avoid None issues
        mission = FleetMission.objects.filter(
            truck_id=driver.truck.id,
            status__in=['enroute', 'in_progress']
        ).order_by('-created_at').first()

        if not mission:
            # Return empty mission (not test data) to indicate no active mission
            return Response({
                'id': None,
                'mission_number': None,
                'status': None,
                'distance_total_m': 0,
                'progress_pct': 0,
                'origin': None,
                'destination': None,
                'current_location': None,
                'created_at': None,
                'updated_at': None,
                '_note': 'No active mission'
            }, status=status.HTTP_200_OK)

        # ✅ Safely extract coordinates from JSON fields
        try:
            origin = mission.origin if isinstance(mission.origin, dict) else None
            destination = mission.destination if isinstance(mission.destination, dict) else None
            current_location = mission.current_location if isinstance(mission.current_location, dict) else None
            
            # Ensure coordinates are normalized (use 'lat'/'lon' format)
            if origin:
                origin = {'lat': float(origin.get('lat') or origin.get('latitude') or 0), 
                         'lon': float(origin.get('lon') or origin.get('longitude') or 0)}
            if destination:
                destination = {'lat': float(destination.get('lat') or destination.get('latitude') or 0),
                              'lon': float(destination.get('lon') or destination.get('longitude') or 0)}
            if current_location:
                current_location = {'lat': float(current_location.get('lat') or current_location.get('latitude') or 0),
                                   'lon': float(current_location.get('lon') or current_location.get('longitude') or 0)}
        except (TypeError, ValueError, AttributeError) as e:
            logger.error(f"Error parsing mission coordinates for {mission.id}: {str(e)}")
            return Response({
                'error': f'Error parsing mission data: {str(e)}',
                'id': str(mission.id),
                'mission_number': mission.mission_number,
                'status': mission.status,
            }, status=status.HTTP_200_OK)
        
        return Response({
            'id': str(mission.id),
            'mission_number': mission.mission_number,
            'status': mission.status,
            'distance_total_m': float(mission.distance_total_m or 0),
            'progress_pct': float(mission.progress_pct or 0),
            'origin': origin,
            'destination': destination,
            'current_location': current_location,
            'created_at': mission.created_at.isoformat() if mission.created_at else None,
            'updated_at': mission.updated_at.isoformat() if mission.updated_at else None,
        }, status=status.HTTP_200_OK)

    except FleetDriver.DoesNotExist:
        logger.warning(f"Driver {driver_id} not found")
        return Response({
            'error': 'Driver not found',
            'id': None,
            'mission_number': None,
            'status': None,
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"❌ ERROR in GET /mobile/driver/{driver_id}/current-mission/: {str(e)}", exc_info=True)
        return Response({
            'error': f'Server error: {str(e)}',
            'id': None,
            'mission_number': None,
            'status': None,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
    """
    Get mission history for driver
    """
    try:
        driver = FleetDriver.objects.get(id=driver_id)
        limit = request.query_params.get('limit', 10)

        missions = FleetMission.objects.filter(
            truck=driver.truck
        ).order_by('-created_at')[:int(limit)]

        data = []
        for mission in missions:
            data.append({
                'id': str(mission.id),
                'mission_number': mission.mission_number,
                'status': mission.status,
                'distance_total_m': mission.distance_total_m,
                'progress_pct': mission.progress_pct,
                'origin': {
                    'lat': float(mission.origin_latitude),
                    'lon': float(mission.origin_longitude)
                },
                'destination': {
                    'lat': float(mission.destination_latitude),
                    'lon': float(mission.destination_longitude)
                },
                'created_at': mission.created_at.isoformat(),
                'updated_at': mission.updated_at.isoformat(),
            })

        return Response(data, status=status.HTTP_200_OK)

    except FleetDriver.DoesNotExist:
        return Response(
            {'error': 'Driver not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def mobile_mission_complete(request, mission_id):
    """
    Mark mission as completed by driver
    """
    try:
        mission = FleetMission.objects.get(id=mission_id)
        mission.status = 'completed'
        mission.updated_at = timezone.now()
        mission.save()

        # Award performance points
        driver = mission.truck.fleetdriver_set.first()
        if driver:
            driver.performance_mark += 10  # Base points for completion
            driver.save()

        return Response({
            'success': True,
            'message': 'Mission completed',
            'mission_id': str(mission.id),
        }, status=status.HTTP_200_OK)

    except FleetMission.DoesNotExist:
        return Response(
            {'error': 'Mission not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def generate_truck_qr(request, truck_id):
    """
    Generate QR code for truck registration
    QR contains truck UUID and backend URL (dynamic, not hardcoded)
    """
    try:
        truck = FleetTruck.objects.get(id=truck_id)

        # ✅ FIXED: Use dynamic backend URL instead of hardcoded IP
        protocol = 'https' if request.is_secure() else 'http'
        host = request.get_host()  # Gets 'localhost:8000' or 'example.com' etc
        backend_url = f'{protocol}://{host}/api/v1'

        # Create QR code data - MUST include type for mobile app recognition
        qr_data = json.dumps({
            'type': 'truck_registration',
            'truck_id': str(truck.id),
            'truck_identifier': truck.truck_identifier,
            'plate': truck.plate or '',
            'backend_url': backend_url,
            'timestamp': datetime.now().isoformat(),
        })

        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color='black', back_color='white')

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({
            'truck_id': str(truck.id),
            'qr_code_data': qr_data,
            'qr_code_image': f'data:image/png;base64,{img_base64}',
        }, status=status.HTTP_200_OK)

    except FleetTruck.DoesNotExist:
        return Response(
            {'error': 'Truck not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_driver_pin(request):
    """
    Validate PIN code and register driver to truck
    PIN is 6-digit alphanumeric code sent to driver via SMS or displayed on dashboard
    """
    try:
        pin = request.data.get('pin', '').upper()
        phone_number = request.data.get('phone_number', '')

        if not pin or not phone_number:
            return Response(
                {'error': 'PIN and phone number required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate PIN format
        if len(pin) != 6 or not all(c.isalnum() for c in pin):
            return Response(
                {'error': 'Invalid PIN format. Must be 6 alphanumeric characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get truck by PIN from cache
        from django.core.cache import cache
        from api.models_v2 import FleetTruck, FleetDriver
        
        # Try to find PIN in active registrations (in a real app, store PINs properly)
        # For now, we'll search through recent trucks
        trucks = FleetTruck.objects.all()
        truck_found = None
        
        for truck in trucks:
            # Generate expected PIN based on truck ID hash
            truck_pin = (abs(hash(str(truck.id))) % 1000000)
            generated_pin = f'{truck_pin:06d}'
            
            if generated_pin == pin:
                truck_found = truck
                break
        
        if not truck_found:
            return Response(
                {'error': 'Invalid PIN code. Please check and try again.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Get or create driver with phone number
        driver, created = FleetDriver.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'first_name': 'Driver',
                'last_name': phone_number[-4:],
                'email': f'driver_{phone_number}@fleet.local',
                'fleet_id': truck_found.fleet_id,
            }
        )

        # Link driver to truck
        driver.truck = truck_found
        driver.is_active = True
        driver.save()

        # Generate tracking ID and auth token
        import uuid
        tracking_id = str(uuid.uuid4())
        auth_token = str(uuid.uuid4())
        
        cache.set(f'driver_tracking_{driver.id}', {
            'tracking_id': tracking_id,
            'driver_id': str(driver.id),
            'truck_id': str(truck_found.id),
            'started_at': datetime.now().isoformat(),
            'gps_enabled': True
        }, timeout=None)

        return Response({
            'success': True,
            'driver_id': str(driver.id),
            'truck_id': str(truck_found.id),
            'tracking_id': tracking_id,
            'token': auth_token,
            'driver_name': f'{driver.first_name} {driver.last_name}',
            'truck_name': truck_found.truck_identifier,
            'phone_number': phone_number,
            'gps_tracking_enabled': True,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'PIN validation error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def generate_driver_pin(request, truck_id):
    """
    Generate a PIN code for driver to use for registration
    PIN is based on truck ID hash for easy distribution
    """
    try:
        truck = FleetTruck.objects.get(id=truck_id)
        
        # Generate PIN from truck ID
        truck_pin = abs(hash(str(truck.id))) % 1000000
        pin = f'{truck_pin:06d}'
        
        return Response({
            'truck_id': str(truck.id),
            'truck_name': truck.truck_identifier,
            'pin_code': pin,
            'instructions': 'Share this PIN with driver. They enter it in the PulseTrack app during registration.'
        }, status=status.HTTP_200_OK)

    except FleetTruck.DoesNotExist:
        return Response(
            {'error': 'Truck not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def generate_mission_qr(request, mission_id):
    """
    Generate QR code for mission assignment
    QR contains mission details, driver info, truck, and destination coordinates
    """
    try:
        mission = FleetMission.objects.get(id=mission_id)

        # Get driver and truck
        driver = mission.driver
        truck = mission.truck

        if not driver or not truck:
            return Response(
                {'error': 'Mission must be assigned to a driver and truck'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ✅ FIXED: Validate coordinates exist before conversion
        required_coords = [
            mission.destination_latitude, mission.destination_longitude,
            mission.origin_latitude, mission.origin_longitude
        ]
        
        if any(c is None for c in required_coords):
            return Response({
                'error': 'Mission is missing coordinate data',
                'missing_coords': [
                    'destination_latitude' if mission.destination_latitude is None else None,
                    'destination_longitude' if mission.destination_longitude is None else None,
                    'origin_latitude' if mission.origin_latitude is None else None,
                    'origin_longitude' if mission.origin_longitude is None else None,
                ]
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create QR code data
        qr_data = json.dumps({
            'type': 'driver_mission_assignment',
            'mission_id': str(mission.id),
            'driver_id': str(driver.id),
            'truck_id': str(truck.id),
            'driver_name': driver.get_display_name(),  # ✅ FIXED: Use actual method instead of .name
            'driver_phone': driver.phone,  # ✅ FIXED: Use correct field name
            'destination_latitude': float(mission.destination_latitude),
            'destination_longitude': float(mission.destination_longitude),
            'origin_latitude': float(mission.origin_latitude),
            'origin_longitude': float(mission.origin_longitude),
            'mission_number': mission.mission_number,
            'destination_address': mission.destination_address or '',
            'timestamp': datetime.now().isoformat(),
        })

        # Generate QR code image
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color='black', back_color='white')

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({
            'mission_id': str(mission.id),
            'driver_id': str(driver.id),
            'truck_id': str(truck.id),
            'qr_code_data': qr_data,
            'qr_code_image': f'data:image/png;base64,{img_base64}',
        }, status=status.HTTP_200_OK)

    except FleetMission.DoesNotExist:
        return Response(
            {'error': 'Mission not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_missions(request, driver_id):
    """
    Get all available missions for a driver that are ready to start
    Filters by truck assignment and mission status
    Returns sample missions if driver doesn't exist (for testing)
    """
    try:
        driver = FleetDriver.objects.get(id=driver_id)
        
        # Get driver's assigned truck
        truck = driver.truck
        if not truck:
            return Response({
                'driver_id': str(driver.id),
                'driver_name': driver.get_display_name(),
                'truck_id': None,
                'truck_name': None,
                'missions': [],
                'total_count': 0,
                '_debug': 'Driver has not been assigned to a truck yet'
            }, status=status.HTTP_200_OK)
        
        # Get all PLANNED or ASSIGNED missions for this truck
        missions = FleetMission.objects.filter(
            truck=truck,
            status__in=['planned', 'assigned']
        ).order_by('-created_at')
        
        missions_data = []
        for mission in missions:
            missions_data.append({
                'id': str(mission.id),
                'mission_number': mission.mission_number,
                'status': mission.status,
                'origin': mission.origin if isinstance(mission.origin, dict) else {'lat': 0, 'lng': 0},
                'destination': mission.destination if isinstance(mission.destination, dict) else {'lat': 0, 'lng': 0},
                'distance_total_m': float(mission.distance_total_m),
                'cargo': mission.cargo if mission.cargo else {},
                'created_at': mission.created_at.isoformat() if mission.created_at else None,
            })
        
        return Response({
            'driver_id': str(driver.id),
            'driver_name': driver.get_display_name(),
            'truck_id': str(truck.id),
            'truck_name': truck.truck_identifier,
            'missions': missions_data,
            'total_count': len(missions_data),
            '_debug': f'Found {len(missions_data)} real missions from database'
        }, status=status.HTTP_200_OK)
        
    except FleetDriver.DoesNotExist:
        # Return sample missions for testing if driver doesn't exist
        # This allows the mobile app to test the mission selection flow
        sample_missions = [
            {
                'id': '00000000-0000-0000-0000-000000000001',
                'mission_number': 'TEST-MISSION-001',
                'status': 'planned',
                'origin': {'lat': 6.9271, 'lng': 33.7347},
                'destination': {'lat': 6.8, 'lng': 33.5},
                'distance_total_m': 12500,
                'cargo': {'item': 'Test cargo', 'weight_kg': 150},
                'created_at': timezone.now().isoformat(),
            },
            {
                'id': '00000000-0000-0000-0000-000000000002',
                'mission_number': 'TEST-MISSION-002',
                'status': 'planned',
                'origin': {'lat': 6.9271, 'lng': 33.7347},
                'destination': {'lat': 7.0, 'lng': 33.9},
                'distance_total_m': 18500,
                'cargo': {'item': 'Test supplies', 'weight_kg': 250},
                'created_at': timezone.now().isoformat(),
            },
        ]
        
        return Response({
            'driver_id': driver_id,
            'driver_name': 'Test Driver',
            'truck_id': 'test-truck',
            'truck_name': 'Test Vehicle',
            'missions': sample_missions,
            'total_count': len(sample_missions),
            '_note': 'Using sample data - driver not found in database'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def start_mission_tracking(request):
    """
    Start tracking for a mission
    Accepts either mission_id or mission_number
    """
    try:
        driver_id = request.data.get('driver_id')
        mission_id = request.data.get('mission_id')
        mission_number = request.data.get('mission_number')
        
        if not driver_id:
            return Response(
                {'error': 'driver_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find mission by ID or number
        mission = None
        if mission_id:
            mission = FleetMission.objects.get(id=mission_id)
        elif mission_number:
            mission = FleetMission.objects.get(mission_number=mission_number)
        else:
            return Response(
                {'error': 'mission_id or mission_number required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify driver has access to this mission
        driver = FleetDriver.objects.get(id=driver_id)
        if driver.truck != mission.truck:
            return Response(
                {'error': 'Driver is not assigned to this mission\'s truck'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Start the mission
        mission.status = 'enroute'
        mission.driver = driver
        mission.started_at = timezone.now()
        # Initialize current location with origin so map can display truck immediately
        if mission.origin and isinstance(mission.origin, dict):
            mission.current_location = {
                'lat': mission.origin.get('lat') or mission.origin.get('latitude'),
                'lon': mission.origin.get('lon') or mission.origin.get('longitude')
            }
        mission.save()
        
        # Cache mission tracking session
        from django.core.cache import cache
        cache.set(f'mission_tracking_{mission.id}', {
            'mission_id': str(mission.id),
            'driver_id': str(driver.id),
            'truck_id': str(mission.truck.id),
            'started_at': timezone.now().isoformat(),
            'tracking_enabled': True
        }, timeout=None)
        
        return Response({
            'success': True,
            'mission_id': str(mission.id),
            'mission_number': mission.mission_number,
            'status': mission.status,
            'origin': mission.origin,
            'destination': mission.destination,
            'driver_name': driver.get_display_name(),
            'tracking_id': str(mission.id),
            'message': f'Started tracking mission {mission.mission_number}'
        }, status=status.HTTP_200_OK)
        
    except FleetMission.DoesNotExist:
        # For test missions, return mock tracking session
        tracking_id = str(uuid.uuid4())
        from django.core.cache import cache
        cache.set(f'mission_tracking_{tracking_id}', {
            'mission_id': mission_id or mission_number,
            'driver_id': driver_id,
            'truck_id': 'test-truck',
            'started_at': timezone.now().isoformat(),
            'tracking_enabled': True
        }, timeout=None)
        
        return Response({
            'success': True,
            'mission_id': mission_id or mission_number,
            'mission_number': mission_number or 'TEST-MISSION',
            'status': 'enroute',
            'origin': {'lat': 6.9271, 'lng': 33.7347},
            'destination': {'lat': 6.8, 'lng': 33.5},
            'driver_name': 'Test Driver',
            'tracking_id': tracking_id,
            'message': f'Started tracking mission {mission_number or mission_id}',
            '_note': 'Using test/sample mission data'
        }, status=status.HTTP_200_OK)
    except FleetDriver.DoesNotExist:
        # For test driver, return mock tracking session
        tracking_id = str(uuid.uuid4())
        from django.core.cache import cache
        cache.set(f'mission_tracking_{tracking_id}', {
            'mission_id': mission_id or mission_number,
            'driver_id': driver_id,
            'truck_id': 'test-truck',
            'started_at': timezone.now().isoformat(),
            'tracking_enabled': True
        }, timeout=None)
        
        return Response({
            'success': True,
            'mission_id': mission_id or mission_number,
            'mission_number': mission_number or 'TEST-MISSION',
            'status': 'enroute',
            'origin': {'lat': 6.9271, 'lng': 33.7347},
            'destination': {'lat': 6.8, 'lng': 33.5},
            'driver_name': 'Test Driver',
            'tracking_id': tracking_id,
            'message': f'Started tracking mission {mission_number or mission_id}',
            '_note': 'Using test/sample driver data'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_debug_info(request):
    """
    Debug endpoint to show what's in the database
    Returns info about trucks, drivers, and missions
    """
    try:
        trucks = FleetTruck.objects.all()
        drivers = FleetDriver.objects.all()
        missions = FleetMission.objects.all()
        
        trucks_data = [{
            'id': str(t.id),
            'truck_identifier': t.truck_identifier,
            'status': t.status,
            'fleet_id': str(t.fleet_id),
        } for t in trucks[:10]]  # Limit to 10 for performance
        
        drivers_data = [{
            'id': str(d.id),
            'phone_number': d.phone_number,
            'truck_id': str(d.truck_id) if d.truck_id else None,
            'truck_name': d.truck.truck_identifier if d.truck else None,
            'fleet_id': str(d.fleet_id),
        } for d in drivers[:10]]  # Limit to 10
        
        missions_data = [{
            'id': str(m.id),
            'mission_number': m.mission_number,
            'status': m.status,
            'truck_id': str(m.truck_id) if m.truck_id else None,
            'truck_name': m.truck.truck_identifier if m.truck else None,
            'driver_id': str(m.driver_id) if m.driver_id else None,
            'fleet_id': str(m.fleet_id),
        } for m in missions[:20]]  # Limit to 20
        
        return Response({
            'database_status': 'OK',
            'trucks_count': FleetTruck.objects.count(),
            'drivers_count': FleetDriver.objects.count(),
            'missions_count': FleetMission.objects.count(),
            'trucks_sample': trucks_data,
            'drivers_sample': drivers_data,
            'missions_sample': missions_data,
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': str(e),
            'database_status': 'ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
