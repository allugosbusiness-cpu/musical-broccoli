"""
Truck location and speed tracking endpoints
Real-time location updates from mobile app
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import FleetTruck

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def update_truck_location_speed(request):
    """
    POST /api/v1/truck-tracking/location-speed/
    
    Update truck's current location and speed (called from mobile app every 5 seconds)
    
    Request body:
    {
        "truck_id": "uuid",
        "latitude": -18.975,
        "longitude": 32.655,
        "speed_kmh": 45.5,
        "timestamp": "2026-05-11T04:15:00Z"
    }
    """
    try:
        data = json.loads(request.body)
        truck_id = data.get('truck_id')
        
        if not truck_id:
            return JsonResponse({'error': 'truck_id required'}, status=400)
        
        truck = FleetTruck.objects.get(id=truck_id)
        
        # Update location and speed
        truck.current_location = {
            'lat': float(data.get('latitude', 0)),
            'lon': float(data.get('longitude', 0)),
            'timestamp': data.get('timestamp', timezone.now().isoformat())
        }
        truck.speed_kmh = float(data.get('speed_kmh', 0))
        truck.updated_at = timezone.now()
        
        truck.save()
        
        logger.info(f"📍 Truck {truck.truck_identifier} location updated: {truck.speed_kmh}km/h at {truck.current_location}")
        
        return JsonResponse({
            'status': 'success',
            'truck_id': str(truck.id),
            'truck_identifier': truck.truck_identifier,
            'location': truck.current_location,
            'speed_kmh': float(truck.speed_kmh) if truck.speed_kmh else 0,
            'updated_at': truck.updated_at.isoformat(),
        }, status=200)
        
    except FleetTruck.DoesNotExist:
        logger.error(f"❌ Truck not found: {truck_id}")
        return JsonResponse({'error': 'Truck not found'}, status=404)
    except Exception as e:
        logger.error(f"❌ Location update error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_truck_current_location_speed(request, truck_id):
    """
    GET /api/v1/truck-tracking/location-speed/{truck_id}/
    
    Get truck's current location and speed for web dashboard display
    """
    try:
        truck = FleetTruck.objects.get(id=truck_id)
        
        return JsonResponse({
            'truck_id': str(truck.id),
            'truck_identifier': truck.truck_identifier,
            'plate': truck.plate,
            'status': truck.status,
            'location': truck.current_location or {'lat': 0, 'lon': 0},
            'speed_kmh': float(truck.speed_kmh) if truck.speed_kmh else 0,
            'updated_at': truck.updated_at.isoformat() if truck.updated_at else None,
        }, status=200)
        
    except FleetTruck.DoesNotExist:
        return JsonResponse({'error': 'Truck not found'}, status=404)
    except Exception as e:
        logger.error(f"❌ Get location error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_all_trucks_current_locations(request):
    """
    GET /api/v1/truck-tracking/all-locations/
    
    Get all trucks' current locations and speeds for dashboard map display
    """
    try:
        trucks = FleetTruck.objects.all()
        
        trucks_data = []
        for truck in trucks:
            trucks_data.append({
                'truck_id': str(truck.id),
                'truck_identifier': truck.truck_identifier,
                'plate': truck.plate,
                'status': truck.status,
                'location': truck.current_location or {'lat': 0, 'lon': 0},
                'speed_kmh': float(truck.speed_kmh) if truck.speed_kmh else 0,
                'updated_at': truck.updated_at.isoformat() if truck.updated_at else None,
            })
        
        logger.info(f"📍 Retrieved {len(trucks_data)} truck locations")
        
        return JsonResponse({
            'count': len(trucks_data),
            'trucks': trucks_data,
        }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Get all locations error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
