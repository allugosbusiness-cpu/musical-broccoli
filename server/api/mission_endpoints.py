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
    POST /api/v1/api-missions/create/
    
    Create a new mission
    
    Request body:
    {
        "identifier": "MIS001",
        "truck_id": "uuid",
        "driver_id": "uuid",
        "origin": {"lat": -17.8, "lon": 31.0},
        "destination": {"lat": -17.9, "lon": 31.1},
        "planned_distance_km": 50,
        "planned_duration_minutes": 120
    }
    """
    try:
        data = json.loads(request.body)
        identifier = data.get('identifier', f'MIS-{int(timezone.now().timestamp())}')
        logger.info(f"📝 Creating mission: {identifier}")
        
        # Validate required fields
        if not all(k in data for k in ['truck_id', 'driver_id', 'origin', 'destination']):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        with transaction.atomic():
            # Get truck and driver instances
            truck = FleetTruck.objects.get(id=data['truck_id'])
            driver = FleetDriver.objects.get(id=data['driver_id'])
            
            # Convert km to meters
            distance_m = float(data.get('planned_distance_km', 0)) * 1000
            
            mission = FleetMission.objects.create(
                fleet_id=truck.fleet_id,
                mission_number=identifier,
                truck=truck,
                driver=driver,
                status='pending',
                origin=data['origin'],  # {lat, lon}
                destination=data['destination'],  # {lat, lon}
                distance_total_m=distance_m,
                distance_remaining_m=distance_m,
            )
            
            logger.info(f"✅ Mission created: {mission.mission_number}")
            return JsonResponse({
                'id': str(mission.id),
                'mission_number': mission.mission_number,
                'status': mission.status,
                'truck_id': str(mission.truck.id),
                'driver_id': str(mission.driver.id),
                'distance_m': float(mission.distance_total_m),
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
    PATCH /api/v1/api-missions/{mission_id}/status/
    
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
        
        logger.info(f"🔄 Updating mission {mission.mission_number} from {old_status} to {new_status}")
        
        with transaction.atomic():
            mission.status = new_status
            mission.updated_at = timezone.now()
            
            # Update truck status and current location
            if mission.truck:
                mission.truck.status = 'enroute' if new_status == 'enroute' else 'idle'
                if data.get('current_lat'):
                    mission.truck.current_location = {
                        'lat': data['current_lat'],
                        'lon': data['current_lon']
                    }
                mission.truck.save()
                logger.info(f"  🚚 Truck {mission.truck.truck_identifier} status: {mission.truck.status}")
            
            # When mission completes, save delivered time
            if new_status == 'completed' and old_status != 'completed':
                mission.delivered_at = timezone.now()
                mission.completed_at = timezone.now()
                logger.info(f"  ✅ Mission completed: {mission.mission_number}")
            
            mission.save()
            
            return JsonResponse({
                'id': str(mission.id),
                'mission_number': mission.mission_number,
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


@csrf_exempt
@require_http_methods(["GET"])
def get_mission_details(request, mission_id):
    """
    GET /api/v1/api-missions/{mission_id}/details/
    
    Get full mission details including tracking data
    """
    try:
        mission = FleetMission.objects.get(id=mission_id)
        
        return JsonResponse({
            'id': str(mission.id),
            'mission_number': mission.mission_number,
            'status': mission.status,
            'truck': {
                'id': str(mission.truck.id),
                'truck_identifier': mission.truck.truck_identifier,
                'plate': mission.plate,
            } if mission.truck else None,
            'driver': {
                'id': str(mission.driver.id),
                'name': f"{mission.driver.first_name} {mission.driver.last_name}",
            } if mission.driver else None,
            'origin': mission.origin,
            'destination': mission.destination,
            'distance_total_m': float(mission.distance_total_m),
            'distance_remaining_m': float(mission.distance_remaining_m),
            'progress_pct': float(mission.progress_pct),
            'created_at': mission.created_at.isoformat(),
            'started_at': mission.started_at.isoformat() if mission.started_at else None,
            'completed_at': mission.completed_at.isoformat() if mission.completed_at else None,
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
    POST /api/v1/api-missions/{mission_id}/tracking/
    
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
        "totalDistance": 50.5,
        "totalDuration": 120
    }
    """
    try:
        mission = FleetMission.objects.get(id=mission_id)
        data = json.loads(request.body)
        
        logger.info(f"💾 Saving tracking data for mission {mission.mission_number}")
        
        with transaction.atomic():
            # Save mission events (activities)
            for activity in data.get('activities', []):
                event = FleetMissionEvent.objects.create(
                    mission_id=mission_id,
                    event_type=activity.get('type', 'ACTIVITY'),
                    location=activity.get('location', {}),
                    details=activity.get('details', ''),
                )
                logger.info(f"  📌 Event saved: {event.event_type}")
            
            # Update mission with actual distance and duration
            if data.get('totalDistance'):
                mission.distance_remaining_m = 0
                mission.progress_pct = 100
            
            mission.updated_at = timezone.now()
            mission.save()
            
            logger.info(f"✅ Tracking data saved for mission {mission.mission_number}")
            
            return JsonResponse({
                'id': str(mission.id),
                'mission_number': mission.mission_number,
                'events_saved': len(data.get('activities', [])),
                'alerts_saved': len(data.get('alerts', [])),
            }, status=200)
            
    except FleetMission.DoesNotExist:
        logger.error(f"❌ Mission not found: {mission_id}")
        return JsonResponse({'error': 'Mission not found'}, status=404)
    except Exception as e:
        logger.error(f"❌ Tracking data save error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
