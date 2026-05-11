"""
Mission creation and management endpoints for the PulseTrack API
Provides endpoints for creating, updating, and managing missions
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from api.models_v2 import FleetMission, FleetTruck, FleetDriver, FleetMissionStop, FleetMissionEvent
from django.db import transaction

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def create_mission(request):
    """
    POST /api/v1/missions/create/
    
    Create a new mission
    
    Request body:
    {
        "identifier": "MIS001",
        "truck_id": "uuid",
        "driver_id": "uuid",
        "status": "pending",  # pending, enroute, completed
        "origin": {"lat": -17.8, "lon": 31.0},
        "destination": {"lat": -17.9, "lon": 31.1},
        "planned_distance_km": 50,
        "planned_duration_minutes": 120,
        "notes": "Optional mission notes"
    }
    """
    try:
        data = json.loads(request.body)
        logger.info(f"📝 Creating mission: {data.get('identifier')}")
        
        with transaction.atomic():
            mission = FleetMission.objects.create(
                identifier=data.get('identifier', f'MIS-{timezone.now().timestamp()}'),
                truck_id=data.get('truck_id'),
                driver_id=data.get('driver_id'),
                status=data.get('status', 'pending'),
                origin_lat=data.get('origin', {}).get('lat'),
                origin_lon=data.get('origin', {}).get('lon'),
                destination_lat=data.get('destination', {}).get('lat'),
                destination_lon=data.get('destination', {}).get('lon'),
                planned_distance_km=data.get('planned_distance_km', 0),
                planned_duration_minutes=data.get('planned_duration_minutes', 0),
                notes=data.get('notes', ''),
                status_updated_at=timezone.now(),
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            
            logger.info(f"✅ Mission created: {mission.identifier}")
            return JsonResponse({
                'id': str(mission.id),
                'identifier': mission.identifier,
                'status': mission.status,
                'truck_id': str(mission.truck_id),
                'driver_id': str(mission.driver_id),
                'created_at': mission.created_at.isoformat(),
            }, status=201)
            
    except Exception as e:
        logger.error(f"❌ Mission creation error: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["PATCH"])
def update_mission_status(request, mission_id):
    """
    PATCH /api/v1/missions/{mission_id}/status/
    
    Update mission status and trigger trail activation/deactivation
    
    Request body:
    {
        "status": "enroute",  # pending, enroute, completed
        "current_lat": -17.85,
        "current_lon": 31.05
    }
    """
    try:
        mission = FleetMission.objects.get(id=mission_id)
        data = json.loads(request.body)
        old_status = mission.status
        new_status = data.get('status', mission.status)
        
        logger.info(f"🔄 Updating mission {mission.identifier} from {old_status} to {new_status}")
        
        with transaction.atomic():
            mission.status = new_status
            mission.status_updated_at = timezone.now()
            mission.updated_at = timezone.now()
            
            # Update truck status and current location
            if mission.truck:
                mission.truck.status = 'enroute' if new_status == 'enroute' else 'idle'
                mission.truck.latitude = data.get('current_lat', mission.truck.latitude)
                mission.truck.longitude = data.get('current_lon', mission.truck.longitude)
                mission.truck.save()
                logger.info(f"  🚚 Truck {mission.truck.truck_identifier} status: {mission.truck.status}")
            
            # When mission completes, save all tracking data
            if new_status == 'completed' and old_status != 'completed':
                mission.delivered_at = timezone.now()
                logger.info(f"  ✅ Mission completed: {mission.identifier}")
            
            mission.save()
            
            return JsonResponse({
                'id': str(mission.id),
                'identifier': mission.identifier,
                'status': mission.status,
                'truck_status': mission.truck.status if mission.truck else None,
                'updated_at': mission.updated_at.isoformat(),
            }, status=200)
            
    except FleetMission.DoesNotExist:
        logger.error(f"❌ Mission not found: {mission_id}")
        return JsonResponse({'error': 'Mission not found'}, status=404)
    except Exception as e:
        logger.error(f"❌ Mission status update error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_mission_details(request, mission_id):
    """
    GET /api/v1/missions/{mission_id}/
    
    Get full mission details including tracking data
    """
    try:
        mission = FleetMission.objects.get(id=mission_id)
        
        return JsonResponse({
            'id': str(mission.id),
            'identifier': mission.identifier,
            'status': mission.status,
            'truck': {
                'id': str(mission.truck.id),
                'identifier': mission.truck.truck_identifier,
                'plate': mission.truck.plate,
            } if mission.truck else None,
            'driver': {
                'id': str(mission.driver.id),
                'name': f"{mission.driver.first_name} {mission.driver.last_name}",
            } if mission.driver else None,
            'origin': {
                'lat': mission.origin_lat,
                'lon': mission.origin_lon,
            },
            'destination': {
                'lat': mission.destination_lat,
                'lon': mission.destination_lon,
            },
            'planned_distance_km': mission.planned_distance_km,
            'planned_duration_minutes': mission.planned_duration_minutes,
            'actual_distance_km': mission.actual_distance_km,
            'actual_duration_minutes': mission.actual_duration_minutes,
            'notes': mission.notes,
            'created_at': mission.created_at.isoformat(),
            'started_at': mission.started_at.isoformat() if mission.started_at else None,
            'delivered_at': mission.delivered_at.isoformat() if mission.delivered_at else None,
        }, status=200)
        
    except FleetMission.DoesNotExist:
        return JsonResponse({'error': 'Mission not found'}, status=404)
    except Exception as e:
        logger.error(f"❌ Get mission error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def save_mission_tracking_data(request, mission_id):
    """
    POST /api/v1/missions/{mission_id}/tracking-data/
    
    Save tracking data for completed missions (activities, alerts, routes)
    
    Request body:
    {
        "activities": [
            {
                "type": "MISSION_START",
                "timestamp": "2024-01-01T10:00:00Z",
                "location": {"lat": -17.8, "lon": 31.0},
                "details": "Mission started"
            }
        ],
        "alerts": [
            {
                "type": "SPEED_VIOLATION",
                "timestamp": "2024-01-01T10:05:00Z",
                "location": {"lat": -17.81, "lon": 31.01},
                "speed": 105,
                "speedLimit": 100
            }
        ],
        "routePoints": [
            {
                "latitude": -17.8,
                "longitude": 31.0,
                "speed": 0,
                "timestamp": "2024-01-01T10:00:00Z"
            }
        ],
        "totalDistance": 50.5,
        "totalDuration": 120
    }
    """
    try:
        mission = FleetMission.objects.get(id=mission_id)
        data = json.loads(request.body)
        
        logger.info(f"💾 Saving tracking data for mission {mission.identifier}")
        
        with transaction.atomic():
            # Save mission events (activities)
            for activity in data.get('activities', []):
                event = FleetMissionEvent.objects.create(
                    mission_id=mission_id,
                    event_type=activity.get('type', 'ACTIVITY'),
                    latitude=activity.get('location', {}).get('lat'),
                    longitude=activity.get('location', {}).get('lon'),
                    details=activity.get('details', ''),
                    created_at=timezone.now(),
                )
                logger.info(f"  📌 Event saved: {event.event_type}")
            
            # Update mission with actual distance and duration
            if data.get('totalDistance'):
                mission.actual_distance_km = data['totalDistance']
            if data.get('totalDuration'):
                mission.actual_duration_minutes = data['totalDuration']
            
            mission.updated_at = timezone.now()
            mission.save()
            
            logger.info(f"✅ Tracking data saved for mission {mission.identifier}")
            
            return JsonResponse({
                'id': str(mission.id),
                'identifier': mission.identifier,
                'actual_distance_km': mission.actual_distance_km,
                'actual_duration_minutes': mission.actual_duration_minutes,
                'events_saved': len(data.get('activities', [])),
                'alerts_saved': len(data.get('alerts', [])),
                'route_points_saved': len(data.get('routePoints', [])),
            }, status=200)
            
    except FleetMission.DoesNotExist:
        logger.error(f"❌ Mission not found: {mission_id}")
        return JsonResponse({'error': 'Mission not found'}, status=404)
    except Exception as e:
        logger.error(f"❌ Tracking data save error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
