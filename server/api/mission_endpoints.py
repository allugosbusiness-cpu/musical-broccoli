from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db import connection
from .models import FleetDriver, FleetTruck, FleetMission


@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_missions(request, driver_id):
    """
    Get all available missions for a driver that are ready to start
    Filters by truck assignment and mission status
    """
    try:
        driver = FleetDriver.objects.get(id=driver_id)
        
        # Get driver's assigned truck
        truck = driver.truck
        if not truck:
            return Response(
                {'missions': [], 'message': 'Driver has not been assigned to a truck yet'},
                status=status.HTTP_200_OK
            )
        
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
            'total_count': len(missions_data)
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


def _safe_create_mission(data):
    """
    Safely create a mission even when optional columns are missing from the database.
    This handles the case where max_speed, avg_speed, and compressed_trail columns
    don't exist in the production database.
    """
    try:
        # Check which columns exist in the database
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'fleet_missions' 
                AND column_name IN ('max_speed', 'avg_speed', 'compressed_trail')
            """)
            existing_columns = {row[0] for row in cursor.fetchall()}
        
        # Prepare data for insertion
        create_data = data.copy()
        
        # Remove columns that don't exist in the database
        if 'max_speed' not in existing_columns:
            create_data.pop('max_speed', None)
        if 'avg_speed' not in existing_columns:
            create_data.pop('avg_speed', None)
        if 'compressed_trail' not in existing_columns:
            create_data.pop('compressed_trail', None)
        
        # Create the mission using safe method
        mission = FleetMission.objects.create(**create_data)
        
        # Set default values for missing columns after creation
        if 'max_speed' not in existing_columns:
            mission.max_speed = 0
        if 'avg_speed' not in existing_columns:
            mission.avg_speed = 0
        if 'compressed_trail' not in existing_columns:
            mission.compressed_trail = []
        
        # Save only if we need to set computed values
        if any(col not in existing_columns for col in ['max_speed', 'avg_speed', 'compressed_trail']):
            mission.save(update_fields=['max_speed', 'avg_speed', 'compressed_trail'])
        
        return mission
    except Exception as e:
        raise Exception(f"Failed to create mission: {str(e)}")


@api_view(['POST'])
@permission_classes([AllowAny])
def create_mission(request):
    """
    Create a new mission with graceful handling of missing database columns.
    This endpoint works even when max_speed, avg_speed, and compressed_trail columns
    are missing from the production database.
    """
    try:
        # Get required fields
        mission_number = request.data.get('mission_number')
        if not mission_number:
            return Response(
                {'error': 'mission_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if mission already exists
        if FleetMission.objects.filter(mission_number=mission_number).exists():
            return Response(
                {'error': f'Mission {mission_number} already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare mission data
        mission_data = {
            'mission_number': mission_number,
            'status': request.data.get('status', 'planned'),
            'priority': request.data.get('priority', 'normal'),
            'origin': request.data.get('origin', {}),
            'destination': request.data.get('destination', {}),
            'distance_total_m': request.data.get('distance_total_m', 0),
            'progress_pct': request.data.get('progress_pct', 0),
            'cargo': request.data.get('cargo', {}),
            'mission_date': request.data.get('mission_date'),
        }
        
        # Handle truck assignment
        truck_identifier = request.data.get('truck')
        if truck_identifier:
            truck = FleetTruck.objects.filter(
                truck_identifier=truck_identifier
            ).first()
            if not truck:
                return Response(
                    {'error': f'Truck {truck_identifier} not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            mission_data['truck'] = truck
        
        # Handle driver assignment
        driver_identifier = request.data.get('driver')
        if driver_identifier:
            driver = FleetDriver.objects.filter(
                phone_number=driver_identifier
            ).first()
            if not driver:
                return Response(
                    {'error': f'Driver {driver_identifier} not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            mission_data['driver'] = driver
        
        # Create mission safely
        mission = _safe_create_mission(mission_data)
        
        return Response({
            'success': True,
            'mission_id': str(mission.id),
            'mission_number': mission.mission_number,
            'status': mission.status,
            'origin': mission.origin,
            'destination': mission.destination,
            'truck_name': mission.truck.truck_identifier if mission.truck else None,
            'driver_name': mission.driver.get_display_name() if mission.driver else None,
            'max_speed': mission.max_speed,
            'avg_speed': mission.avg_speed,
            'compressed_trail': mission.compressed_trail,
            'created_at': mission.created_at.isoformat(),
            'message': f'Mission {mission.mission_number} created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def start_mission_tracking(request):
    """
    Start tracking for a mission
    Accepts either mission_id or mission_number
    Optional: latitude, longitude for driver's current location
    """
    try:
        driver_id = request.data.get('driver_id')
        mission_id = request.data.get('mission_id')
        mission_number = request.data.get('mission_number')
        # Accept current location from mobile app
        current_latitude = request.data.get('latitude')
        current_longitude = request.data.get('longitude')
        
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
        
        # Initialize origin with driver's actual location if provided
        # This ensures the truck pin appears on the map at the correct location immediately
        if current_latitude is not None and current_longitude is not None:
            try:
                mission.origin = {
                    'lat': float(current_latitude),
                    'lon': float(current_longitude)
                }
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f'Mission {mission.id} initialized with driver current location: ({current_latitude}, {current_longitude})')
            except (ValueError, TypeError):
                pass
        
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