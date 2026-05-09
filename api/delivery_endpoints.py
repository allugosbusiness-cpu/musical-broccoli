# server/api/delivery_endpoints.py
"""
Delivery confirmation endpoints for mobile app
Handles mission delivery detection and driver status updates
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models_v2 import FleetDriver, FleetTruck, FleetMission, FleetMissionEvent, MissionEventType, MissionStatus


@api_view(['POST'])
@permission_classes([AllowAny])
def mission_delivery_confirmed(request, mission_id):
    """
    Confirm that driver has reached destination and mission is delivered.
    Called by mobile app when geofence is triggered (within 100m of destination)
    
    Request body:
    {
        'driver_id': 'driver-uuid',
        'delivered_at': '2026-05-08T14:30:00Z',
        'delivery_timestamp': 1715254200000
    }
    """
    try:
        driver_id = request.data.get('driver_id')
        delivered_at_str = request.data.get('delivered_at')
        delivery_timestamp = request.data.get('delivery_timestamp')

        # Validate required fields
        if not driver_id or not delivered_at_str:
            return Response(
                {'error': 'driver_id and delivered_at required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get mission
        try:
            mission = FleetMission.objects.get(id=mission_id)
        except FleetMission.DoesNotExist:
            return Response(
                {'error': 'Mission not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify driver matches mission
        if str(mission.driver_id) != driver_id:
            return Response(
                {'error': 'Driver does not match mission'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Parse delivered_at timestamp
        try:
            if delivered_at_str:
                delivered_at = datetime.fromisoformat(delivered_at_str.replace('Z', '+00:00'))
            else:
                delivered_at = timezone.now()
        except (ValueError, TypeError):
            delivered_at = timezone.now()

        # Update mission
        mission.status = MissionStatus.COMPLETED
        mission.delivered_at = delivered_at
        mission.completed_at = delivered_at
        mission.updated_at = timezone.now()
        mission.save()

        # Update driver status - now free for next mission
        driver = mission.driver
        if driver:
            driver.on_duty = False  # Driver is now available
            driver.last_active_at = timezone.now()
            driver.save()

            # Increment deliveries count
            driver.deliveries_count = (driver.deliveries_count or 0) + 1
            driver.save(update_fields=['deliveries_count'])

        # Update truck status - idle since mission completed
        truck = mission.truck
        if truck:
            truck.status = 'idle'
            truck.updated_at = timezone.now()
            truck.save()

        # Create event log for delivery
        FleetMissionEvent.objects.create(
            mission=mission,
            truck=truck,
            driver=driver,
            event_type=MissionEventType.STATUS_CHANGED,
            payload={
                'from_status': 'in_progress',
                'to_status': 'completed',
                'delivered_at': delivered_at.isoformat(),
                'delivery_method': 'geofence_detection'
            }
        )

        return Response({
            'success': True,
            'message': f'Mission {mission.mission_number} delivered successfully',
            'mission_id': str(mission.id),
            'delivered_at': delivered_at.isoformat(),
            'driver_name': driver.get_display_name() if driver else 'Unknown',
            'driver_is_free': True,
            'driver_deliveries_count': driver.deliveries_count if driver else 0
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def driver_status(request, driver_id):
    """
    Get current driver status (free/busy, available for next mission)
    """
    try:
        driver = FleetDriver.objects.get(id=driver_id)

        # Get current mission if any
        current_mission = FleetMission.objects.filter(
            driver=driver,
            status__in=['assigned', 'enroute']
        ).first()

        return Response({
            'driver_id': str(driver.id),
            'driver_name': driver.get_display_name(),
            'is_free': not driver.on_duty,
            'on_duty': driver.on_duty,
            'current_mission_id': str(current_mission.id) if current_mission else None,
            'deliveries_today': driver.deliveries_count,
            'last_delivery': driver.updated_at.isoformat() if driver.updated_at else None,
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
def mission_details(request, mission_id):
    """
    Get mission details including destination coordinates for geofencing
    Used by mobile app to set up delivery detection parameters
    """
    try:
        mission = FleetMission.objects.get(id=mission_id)

        destination = mission.destination
        dest_lat = destination.get('lat') or destination.get('latitude')
        dest_lon = destination.get('lon') or destination.get('longitude')

        return Response({
            'mission_id': str(mission.id),
            'mission_number': mission.mission_number,
            'status': mission.status,
            'driver_id': str(mission.driver_id) if mission.driver_id else None,
            'truck_id': str(mission.truck_id) if mission.truck_id else None,
            'destination': {
                'latitude': float(dest_lat) if dest_lat else None,
                'longitude': float(dest_lon) if dest_lon else None,
            },
            'distance_total_m': float(mission.distance_total_m) if mission.distance_total_m else 0,
            'distance_remaining_m': float(mission.distance_remaining_m) if mission.distance_remaining_m else 0,
            'progress_pct': float(mission.progress_pct) if mission.progress_pct else 0,
            'delivered_at': mission.delivered_at.isoformat() if mission.delivered_at else None,
            'is_delivered': mission.delivered_at is not None,
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
