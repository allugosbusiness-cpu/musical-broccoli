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
from io import BytesIO
import base64
from datetime import datetime, timedelta

from .models import FleetDriver, FleetTruck, FleetMission, TruckLocation
from .models import Alert
from .serializers import TruckSerializer, AlertSerializer


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
        driver.status = 'active'
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
        driver.updated_at = timezone.now()
        driver.save()

        # Also update truck's current location so web app can see it
        if driver.truck:
            driver.truck.last_latitude = float(latitude)
            driver.truck.last_longitude = float(longitude)
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
                alert_type='speed',
                severity='high',
                message=f'Overspeeding: {speed} km/h',
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
        severity = 'high' if alert_type in ['overspeeding', 'route_deviation'] else 'medium'
        alert = Alert.objects.create(
            alert_type=alert_type,
            message=message,
            severity=severity,
        )

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
            status__in=['enroute', 'in_progress']
        ).first()

        origin_data = current_mission.get_origin_coords() if current_mission else None
        destination_data = current_mission.get_destination_coords() if current_mission else None

        return Response({
            'id': str(driver.id),
            'name': driver.get_display_name(),
            'phone': driver.phone_number,
            'email': driver.email,
            'performance_points': driver.performance_mark,
            'latitude': driver.latitude,
            'longitude': driver.longitude,
            'truck_id': str(driver.truck.id) if driver.truck else None,
            'truck_name': driver.truck.truck_identifier if driver.truck else None,
            'current_mission': {
                'id': str(current_mission.id),
                'mission_number': current_mission.mission_number,
                'status': current_mission.status,
                'distance_total_m': current_mission.distance_total_m,
                'progress_pct': current_mission.progress_pct,
                'origin': origin_data,
                'destination': destination_data,
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
def mobile_driver_current_mission(request, driver_id):
    """
    Get current mission for driver
    Returns mission details with current location and progress
    """
    try:
        driver = FleetDriver.objects.get(id=driver_id)

        # Look for missions in 'enroute' or 'in_progress' status
        mission = FleetMission.objects.filter(
            truck=driver.truck,
            status__in=['enroute', 'in_progress']
        ).first()

        if not mission:
            return Response(
                {'error': 'No active mission'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Extract coordinates from mission origin/destination JSONFields
        origin_data = mission.get_origin_coords()
        destination_data = mission.get_destination_coords()

        return Response({
            'id': str(mission.id),
            'mission_number': mission.mission_number,
            'status': mission.status,
            'distance_total_m': float(mission.distance_total_m) if mission.distance_total_m else 0,
            'progress_pct': float(mission.progress_pct) if mission.progress_pct else 0,
            'origin': origin_data,
            'destination': destination_data,
            'current_location': origin_data,
            'driver_id': str(driver.id),
            'truck_id': str(mission.truck.id),
            'created_at': mission.created_at.isoformat() if mission.created_at else None,
            'updated_at': mission.updated_at.isoformat() if mission.updated_at else None,
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
def mobile_driver_missions(request, driver_id):
    """
    Get mission history for driver
    Returns list of missions with coordinates in both old and new formats
    """
    try:
        driver = FleetDriver.objects.get(id=driver_id)
        limit = request.query_params.get('limit', 10)

        missions = FleetMission.objects.filter(
            truck=driver.truck
        ).order_by('-created_at')[:int(limit)]

        data = []
        for mission in missions:
            origin_data = mission.get_origin_coords()
            destination_data = mission.get_destination_coords()
            
            data.append({
                'id': str(mission.id),
                'mission_number': mission.mission_number,
                'status': mission.status,
                'distance_total_m': float(mission.distance_total_m) if mission.distance_total_m else 0,
                'progress_pct': float(mission.progress_pct) if mission.progress_pct else 0,
                'origin': origin_data,
                'destination': destination_data,
                'created_at': mission.created_at.isoformat() if mission.created_at else None,
                'updated_at': mission.updated_at.isoformat() if mission.updated_at else None,
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
        mission = FleetMission.objects.filter(id=mission_id).first()
        if not mission:
            return Response(
                {'error': 'Mission not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
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

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def generate_truck_qr(request, truck_id):
    """
    Generate QR code for truck registration
    QR contains truck UUID and backend URL
    """
    try:
        truck = FleetTruck.objects.get(id=truck_id)

        # Create QR code data - MUST include type for mobile app recognition
        qr_data = json.dumps({
            'type': 'truck_registration',
            'truck_id': str(truck.id),
            'truck_identifier': truck.truck_identifier,
            'plate': truck.plate or '',
            'backend_url': 'http://192.168.1.100:8000/api/v1',
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
    Updated: Accepts latitude/longitude, records location history for audit trail
    """
    try:
        pin = request.data.get('pin', '').upper()
        phone_number = request.data.get('phone_number', '')
        # Get current location from mobile app for audit trail
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        accuracy = request.data.get('accuracy', 0)
        altitude = request.data.get('altitude', 0)

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
        driver.status = 'active'
        # Update driver's current location if provided
        if latitude is not None and longitude is not None:
            driver.latitude = float(latitude)
            driver.longitude = float(longitude)
        driver.save()

        # Override truck's current location with driver's actual location
        if latitude is not None and longitude is not None:
            truck_found.last_latitude = float(latitude)
            truck_found.last_longitude = float(longitude)
            truck_found.last_location_ts = timezone.now()
            truck_found.save()
            
            # Record location history entry for audit trail
            TruckLocation.objects.create(
                truck=truck_found,
                driver=driver,
                latitude=float(latitude),
                longitude=float(longitude),
                speed=0,
                accuracy=float(accuracy) if accuracy else 0,
                altitude=float(altitude) if altitude else 0,
                timestamp=timezone.now()
            )
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Truck {truck_found.truck_identifier} location recorded on driver link: ({latitude}, {longitude})')

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
            'location_synced': latitude is not None and longitude is not None,
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

        # Get coordinates safely
        origin_coords = mission.get_origin_coords()
        destination_coords = mission.get_destination_coords()

        # Create QR code data
        qr_data = json.dumps({
            'type': 'driver_mission_assignment',
            'mission_id': str(mission.id),
            'driver_id': str(driver.id),
            'truck_id': str(truck.id),
            'driver_name': driver.get_display_name(),
            'driver_phone': driver.phone_number,
            'destination_latitude': destination_coords['lat'],
            'destination_longitude': destination_coords['lon'],
            'origin_latitude': origin_coords['lat'],
            'origin_longitude': origin_coords['lon'],
            'mission_number': mission.mission_number,
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
        
        # If very few missions for this truck, also show missions without a truck assignment
        # This handles cases where missions exist but aren't linked to the truck yet
        if missions.count() < 5:
            missions_without_truck = FleetMission.objects.filter(
                truck__isnull=True,
                status__in=['planned', 'assigned']
            ).order_by('-created_at')[:10]
            
            all_missions_list = list(missions) + list(missions_without_truck)
            missions = all_missions_list
        else:
            missions = list(missions)
        
        missions_data = []
        for mission in missions:
            missions_data.append({
                'id': str(mission.id),
                'mission_number': mission.mission_number,
                'status': mission.status,
                'origin': mission.origin if isinstance(mission.origin, dict) else {'lat': 0, 'lng': 0},
                'destination': mission.destination if isinstance(mission.destination, dict) else {'lat': 0, 'lng': 0},
                'distance_total_m': float(mission.distance_total_m) if mission.distance_total_m else 0,
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
            '_debug': f'Truck: {truck.truck_identifier} - Found {len(missions_data)} available missions'
        }, status=status.HTTP_200_OK)
        
    except FleetDriver.DoesNotExist:
        # Return sample missions for testing if driver doesn't exist
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
    Updated: Accepts latitude/longitude, records location history for audit trail
    """
    try:
        driver_id = request.data.get('driver_id')
        mission_id = request.data.get('mission_id')
        mission_number = request.data.get('mission_number')
        # Get current location from mobile app for audit trail
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        accuracy = request.data.get('accuracy', 0)
        altitude = request.data.get('altitude', 0)
        
        if not driver_id:
            return Response(
                {'error': 'driver_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find mission by ID or number
        mission = None
        if mission_id:
            mission = FleetMission.objects.filter(id=mission_id).first()
        elif mission_number:
            mission = FleetMission.objects.filter(mission_number=mission_number).first()
        else:
            return Response(
                {'error': 'mission_id or mission_number required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not mission:
            # For test missions, return mock tracking session
            import uuid
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
                '_note': 'Using test data - mission not found in database'
            }, status=status.HTTP_200_OK)
        
        # Verify driver has access to this mission
        driver = FleetDriver.objects.filter(id=driver_id).first()
        if not driver:
            return Response(
                {'error': 'Driver not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if driver.truck != mission.truck:
            return Response(
                {'error': 'Driver is not assigned to this mission\'s truck'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Start the mission
        mission.status = 'enroute'
        mission.driver = driver
        mission.started_at = timezone.now()
        
        # Initialize current location to origin coordinates
        # This ensures the truck pin appears on the map when mission starts
        if mission.origin:
            if isinstance(mission.origin, dict):
                lat = mission.origin.get('lat', mission.origin.get('latitude', 0))
                lon = mission.origin.get('lon', mission.origin.get('lng', mission.origin.get('longitude', 0)))
                mission.origin['lat'] = lat
                mission.origin['lon'] = lon
        
        # Override mission origin with driver's actual location if provided
        if latitude is not None and longitude is not None:
            mission.origin = {
                'lat': float(latitude),
                'lon': float(longitude)
            }
        
        mission.save()
        
        # Record location history entry for audit trail AND update truck's current coordinates
        if latitude is not None and longitude is not None:
            TruckLocation.objects.create(
                truck=mission.truck,
                driver=driver,
                latitude=float(latitude),
                longitude=float(longitude),
                speed=0,
                accuracy=float(accuracy) if accuracy else 0,
                altitude=float(altitude) if altitude else 0,
                timestamp=timezone.now()
            )
            
            # Update truck's current location fields so web app can access them
            mission.truck.last_latitude = float(latitude)
            mission.truck.last_longitude = float(longitude)
            mission.truck.save()
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Mission {mission.mission_number} location recorded on start: ({latitude}, {longitude})')
        
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
            'message': f'Started tracking mission {mission.mission_number}',
            'location_synced': latitude is not None and longitude is not None
        }, status=status.HTTP_200_OK)
        
    except FleetMission.DoesNotExist:
        # For test missions, return mock tracking session
        import uuid
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
            '_note': 'Using test data - mission not found in database'
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
@permission_classes([AllowAny])
def mobile_debug_info(request):
    """
    Debug endpoint to check API availability and database connectivity
    """
    try:
        # Test database connectivity
        driver_count = FleetDriver.objects.count()
        truck_count = FleetTruck.objects.count()
        mission_count = FleetMission.objects.count()
        
        return Response({
            'status': 'ok',
            'timestamp': timezone.now().isoformat(),
            'database': {
                'connected': True,
                'drivers': driver_count,
                'trucks': truck_count,
                'missions': mission_count
            },
            'api_version': 'v1',
            'endpoints': {
                'available_missions': '/api/v1/mobile/driver/<driver_id>/available-missions/',
                'start_tracking': '/api/v1/mobile/mission/start-tracking/',
                'alert': '/api/v1/mobile/alert/',
                'current_mission': '/api/v1/mobile/driver/<driver_id>/current-mission/'
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e),
            'database': {
                'connected': False
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)