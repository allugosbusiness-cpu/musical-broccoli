"""
Trail Audit Endpoints
Provides full GPS trail data with audit log for each truck.
Trail is stored in FleetActivity as "trail_recorded" entries
and in TruckLocation records (the raw GPS trail).

Supports the web app drawing the full trail of where the mobile app has been.
"""
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Min, Max
from django.utils import timezone
from datetime import timedelta
from .models import FleetActivity, FleetTruck, FleetDriver, FleetMission, TruckLocation

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def truck_trail_audit(request, truck_id):
    """
    GET /api/v1/trucks/<truck_id>/trail-audit/?days=30&limit=500
    
    Returns the FULL GPS trail + activity audit logs for a truck.
    This is used by the web app to draw the trail of where the mobile app has been.
    
    Response:
    {
        "truck_id": "uuid",
        "truck_identifier": "Truck-001",
        "plate": "ABC123",
        "driver_name": "John Doe",
        "trail": [
            {
                "latitude": -18.975,
                "longitude": 32.655,
                "speed": 45.5,
                "accuracy": 10,
                "altitude": 1200,
                "timestamp": "2026-05-11T04:15:00Z",
                "sequence": 1
            }
        ],
        "audit_log": [
            {
                "id": "uuid",
                "activity_type": "trail_recorded",
                "activity_type_display": "Trail Recorded",
                "location": "Mutare CBD",
                "speed_kmh": 45.5,
                "distance_m": 1234.5,
                "timestamp": "2026-05-11T04:15:00Z",
                "notes": "Trail segment recorded: 15 points"
            }
        ],
        "stats": {
            "total_points": 1500,
            "total_distance_km": 245.5,
            "avg_speed": 55.2,
            "max_speed": 95.0,
            "start_time": "2026-05-10T08:00:00Z",
            "end_time": "2026-05-11T04:15:00Z",
            "duration_hours": 20.25,
            "trail_segments": 12
        },
        "count": 1500
    }
    """
    try:
        # Validate truck exists
        try:
            truck = FleetTruck.objects.get(id=truck_id)
        except FleetTruck.DoesNotExist:
            # Try by truck_identifier
            truck = FleetTruck.objects.filter(truck_identifier=truck_id).first()
        except (ValueError, TypeError):
            # Invalid UUID format - try truck_identifier
            truck = FleetTruck.objects.filter(truck_identifier=truck_id).first()
        
        if not truck:
            return JsonResponse({
                'error': f'Truck "{truck_id}" not found',
                'truck_id': truck_id,
                'trail': [],
                'audit_log': [],
                'count': 0
            }, status=404)
        
        # Parse query parameters
        days = int(request.GET.get('days', 30))
        limit = int(request.GET.get('limit', 500))
        try:
            limit = min(limit, 5000)  # Cap at 5000 points
        except (TypeError, ValueError):
            limit = 500
        
        # Calculate start date
        start_date = timezone.now() - timedelta(days=days)
        
        # Get location trail from TruckLocation records
        locations = TruckLocation.objects.filter(
            truck=truck,
            timestamp__gte=start_date
        ).order_by('-timestamp')[:limit]
        
        # Build trail in chronological order
        trail = []
        reversed_locations = list(reversed(locations))
        for i, loc in enumerate(reversed_locations):
            trail_point = {
                'latitude': float(loc.latitude),
                'longitude': float(loc.longitude),
                'speed': float(loc.speed),
                'accuracy': float(loc.accuracy),
                'altitude': float(loc.altitude),
                'timestamp': loc.timestamp.isoformat(),
                'sequence': i + 1,
            }
            
            # Calculate direction/bearing to next point if available
            if i < len(reversed_locations) - 1:
                next_loc = reversed_locations[i + 1]
                from math import atan2, degrees, sqrt
                dlat = float(next_loc.latitude) - float(loc.latitude)
                dlon = float(next_loc.longitude) - float(loc.longitude)
                bearing = degrees(atan2(dlon, dlat)) % 360
                trail_point['bearing'] = round(bearing, 1)
            
            trail.append(trail_point)
        
        # Get the driver associated with the truck's latest location
        latest_location = TruckLocation.objects.filter(truck=truck).order_by('-timestamp').first()
        driver_name = None
        if latest_location and latest_location.driver:
            driver_name = latest_location.driver.get_display_name()
        
        # Get audit trail from FleetActivity
        audit_logs = FleetActivity.objects.filter(
            truck=truck,
            timestamp__gte=start_date
        ).order_by('-timestamp')[:100]
        
        audit_log = []
        for activity in audit_logs:
            audit_entry = {
                'id': str(activity.id),
                'activity_type': activity.activity_type,
                'activity_type_display': activity.get_activity_type_display(),
                'activity_category': activity.activity_category,
                'location_lat': float(activity.location_lat) if activity.location_lat else None,
                'location_lon': float(activity.location_lon) if activity.location_lon else None,
                'location_name': activity.location_name or activity.display_location,
                'speed_kmh': float(activity.speed_kmh) if activity.speed_kmh else None,
                'distance_m': float(activity.distance_m) if activity.distance_m else None,
                'timestamp': activity.timestamp.isoformat(),
                'notes': activity.notes,
                'alert_level': activity.alert_level,
                'is_critical': activity.is_critical,
            }
            audit_log.append(audit_entry)
        
        # Calculate statistics
        stats = {}
        if trail:
            coords = [(p['latitude'], p['longitude']) for p in trail]
            speeds = [p['speed'] for p in trail]
            
            # Total distance (approximate using Haversine)
            total_distance_km = 0
            for i in range(1, len(coords)):
                from math import radians, sin, cos, sqrt, asin
                lat1, lon1 = coords[i-1]
                lat2, lon2 = coords[i]
                R = 6371
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                total_distance_km += R * c
            
            stats = {
                'total_points': len(trail),
                'total_distance_km': round(total_distance_km, 2),
                'avg_speed': round(sum(speeds) / len(speeds), 2) if speeds else 0,
                'max_speed': round(max(speeds), 2) if speeds else 0,
                'start_time': trail[0]['timestamp'] if trail else None,
                'end_time': trail[-1]['timestamp'] if trail else None,
                'duration_hours': round(
                    (timezone.datetime.fromisoformat(trail[-1]['timestamp'].replace('Z', '+00:00')) -
                     timezone.datetime.fromisoformat(trail[0]['timestamp'].replace('Z', '+00:00'))).total_seconds() / 3600, 2
                ) if len(trail) >= 2 else 0,
                'trail_segments': audit_logs.filter(activity_type='trail_recorded').count() if hasattr(audit_logs, 'filter') else 0,
            }
        
        logger.info(f"🚚 Trail audit for {truck.truck_identifier}: {len(trail)} trail points, {len(audit_log)} audit entries")
        
        response_data = {
            'truck_id': str(truck.id),
            'truck_identifier': truck.truck_identifier,
            'plate': truck.plate,
            'driver_name': driver_name,
            'trail': trail,
            'audit_log': audit_log,
            'stats': stats,
            'count': len(trail),
            'days': days,
        }
        
        return JsonResponse(response_data, status=200)
    
    except Exception as e:
        logger.error(f"❌ Trail audit error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def truck_trail_summary(request, truck_id):
    """
    GET /api/v1/trucks/<truck_id>/trail-summary/?days=7
    
    Lightweight summary of trail data for dashboard display.
    Returns just stats without the full trail points.
    """
    try:
        try:
            truck = FleetTruck.objects.get(id=truck_id)
        except FleetTruck.DoesNotExist:
            truck = FleetTruck.objects.filter(truck_identifier=truck_id).first()
        
        if not truck:
            return JsonResponse({'error': f'Truck "{truck_id}" not found'}, status=404)
        
        days = int(request.GET.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get location stats
        location_stats = TruckLocation.objects.filter(
            truck=truck,
            timestamp__gte=start_date
        ).aggregate(
            total_points=Count('id'),
            earliest=Min('timestamp'),
            latest=Max('timestamp'),
        )
        
        # Get audit stats
        audit_count = FleetActivity.objects.filter(
            truck=truck,
            timestamp__gte=start_date,
            activity_type='trail_recorded'
        ).count()
        
        return JsonResponse({
            'truck_id': str(truck.id),
            'truck_identifier': truck.truck_identifier,
            'plate': truck.plate,
            'stats': {
                'total_gps_points': location_stats.get('total_points', 0),
                'trail_segments_recorded': audit_count,
                'earliest_timestamp': location_stats.get('earliest').isoformat() if location_stats.get('earliest') else None,
                'latest_timestamp': location_stats.get('latest').isoformat() if location_stats.get('latest') else None,
            }
        }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Trail summary error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def all_trucks_trail_summary(request):
    """
    GET /api/v1/trucks/trail-summary/?days=7
    
    Summary of trail data for ALL trucks.
    Used by dashboard to show which trucks have trail data.
    """
    try:
        days = int(request.GET.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        trucks = FleetTruck.objects.all()
        summaries = []
        
        for truck in trucks:
            # Count GPS points in period
            point_count = TruckLocation.objects.filter(
                truck=truck,
                timestamp__gte=start_date
            ).count()
            
            # Get latest location
            latest = TruckLocation.objects.filter(
                truck=truck,
                timestamp__gte=start_date
            ).order_by('-timestamp').first()
            
            summaries.append({
                'truck_id': str(truck.id),
                'truck_identifier': truck.truck_identifier,
                'plate': truck.plate,
                'status': truck.status,
                'trail_points': point_count,
                'has_trail': point_count > 0,
                'last_latitude': float(latest.latitude) if latest else None,
                'last_longitude': float(latest.longitude) if latest else None,
                'last_timestamp': latest.timestamp.isoformat() if latest else None,
            })
        
        return JsonResponse({
            'count': len(summaries),
            'trucks': summaries,
            'days': days
        }, status=200)
        
    except Exception as e:
        logger.error(f"❌ All trucks trail summary error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)