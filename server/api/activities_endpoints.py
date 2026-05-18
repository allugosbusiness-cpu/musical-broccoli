"""
Comprehensive Activity Logging and Audit Trail endpoints
Records all system activities for historical tracking
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
import json
from datetime import datetime, timedelta
from .models import FleetActivity, FleetTruck, FleetDriver, FleetMission

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def log_activity(request):
    """
    POST /api/v1/activities/log/
    
    Log a new activity to the audit trail
    Used by mobile app and backend to record all activities
    
    Request body:
    {
        "truck_id": "uuid",
        "driver_id": "uuid",
        "mission_id": "uuid",
        "activity_type": "trail_recorded|mission_started|speed_recorded|...",
        "activity_category": "mission|location|speed|fuel|alert|breach|driver|maintenance|trail|cargo",
        "location_lat": -18.975,
        "location_lon": 32.655,
        "location_name": "Mutare CBD",
        "speed_kmh": 45.5,
        "distance_m": 1234.5,
        "fuel_liters": 45.2,
        "fuel_percentage": 75.5,
        "alert_level": "low|medium|high|critical",
        "breach_type": "speeding|geofence|maintenance",
        "violation_details": "Speed exceeded 120 km/h",
        "mission_status_before": "enroute",
        "mission_status_after": "enroute",
        "is_critical": false,
        "metadata": {"custom_field": "value"},
        "notes": "Optional notes",
        "timestamp": "2026-05-11T04:15:00Z"
    }
    """
    try:
        data = json.loads(request.body)
        
        # Get timestamp (use provided or current)
        timestamp_str = data.get('timestamp', timezone.now().isoformat())
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = timezone.now()
        
        # Get relationships
        truck = None
        driver = None
        mission = None
        
        truck_id = data.get('truck_id')
        if truck_id:
            try:
                truck = FleetTruck.objects.get(id=truck_id)
            except:
                pass
        
        driver_id = data.get('driver_id')
        if driver_id:
            try:
                driver = FleetDriver.objects.get(id=driver_id)
            except:
                pass
        
        mission_id = data.get('mission_id')
        if mission_id:
            try:
                mission = FleetMission.objects.get(id=mission_id)
            except:
                pass
        
        # Get fleet_id from truck or driver or use first available
        fleet_id = data.get('fleet_id')
        if not fleet_id:
            if truck:
                fleet_id = truck.fleet_id
            elif driver:
                fleet_id = driver.fleet_id
            elif mission:
                fleet_id = mission.fleet_id
            else:
                # Try to get first truck's fleet_id as default, otherwise generate UUID
                try:
                    first_truck = FleetTruck.objects.first()
                    if first_truck:
                        fleet_id = first_truck.fleet_id
                    else:
                        # Generate a default UUID for activities without fleet context
                        import uuid
                        fleet_id = str(uuid.uuid4())
                except:
                    import uuid
                    fleet_id = str(uuid.uuid4())
        
        # Create activity
        activity = FleetActivity.objects.create(
            fleet_id=fleet_id,
            truck=truck,
            driver=driver,
            mission=mission,
            activity_type=data.get('activity_type', 'other'),
            activity_category=data.get('activity_category', 'other'),
            location_lat=data.get('location_lat'),
            location_lon=data.get('location_lon'),
            location_name=data.get('location_name'),
            speed_kmh=data.get('speed_kmh'),
            distance_m=data.get('distance_m'),
            fuel_liters=data.get('fuel_liters'),
            fuel_percentage=data.get('fuel_percentage'),
            alert_level=data.get('alert_level'),
            breach_type=data.get('breach_type'),
            violation_details=data.get('violation_details'),
            mission_status_before=data.get('mission_status_before'),
            mission_status_after=data.get('mission_status_after'),
            metadata=data.get('metadata', {}),
            activity_date=timestamp.date(),
            activity_time=timestamp.time(),
            timestamp=timestamp,
            is_critical=data.get('is_critical', False),
            notes=data.get('notes', ''),
        )
        
        logger.info(f"📝 Activity logged: {activity.get_activity_type_display()} by {truck or driver or 'system'}")
        
        return JsonResponse({
            'status': 'success',
            'activity_id': str(activity.id),
            'activity_type': activity.activity_type,
            'timestamp': activity.timestamp.isoformat(),
        }, status=201)
        
    except Exception as e:
        logger.error(f"❌ Activity logging error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_activities(request):
    """
    GET /api/v1/activities/?truck_id=uuid&driver_id=uuid&days=7&activity_type=trail_recorded&limit=100
    
    Retrieve activities from audit trail
    """
    try:
        # Filtering parameters
        truck_id = request.GET.get('truck_id')
        driver_id = request.GET.get('driver_id')
        mission_id = request.GET.get('mission_id')
        activity_type = request.GET.get('activity_type')
        activity_category = request.GET.get('activity_category')
        days = int(request.GET.get('days', 7))  # Last 7 days by default
        limit = int(request.GET.get('limit', 100))  # Max 100 records
        
        # Build query
        query = FleetActivity.objects.all()
        
        # Date range filter
        start_date = timezone.now() - timedelta(days=days)
        query = query.filter(timestamp__gte=start_date)
        
        # Optional filters
        if truck_id:
            query = query.filter(truck_id=truck_id)
        if driver_id:
            query = query.filter(driver_id=driver_id)
        if mission_id:
            query = query.filter(mission_id=mission_id)
        if activity_type:
            query = query.filter(activity_type=activity_type)
        if activity_category:
            query = query.filter(activity_category=activity_category)
        
        # Apply limits
        total_count = query.count()
        activities = query[:limit]
        
        # Format response
        activities_data = []
        for activity in activities:
            activities_data.append({
                'id': str(activity.id),
                'truck_identifier': activity.truck.truck_identifier if activity.truck else None,
                'driver_name': activity.driver.get_display_name() if activity.driver else None,
                'mission_number': activity.mission.mission_number if activity.mission else None,
                'activity_type': activity.activity_type,
                'activity_category': activity.activity_category,
                'activity_type_display': activity.get_activity_type_display(),
                'location': activity.display_location,
                'speed_kmh': float(activity.speed_kmh) if activity.speed_kmh else None,
                'distance_m': float(activity.distance_m) if activity.distance_m else None,
                'fuel_liters': float(activity.fuel_liters) if activity.fuel_liters else None,
                'fuel_percentage': float(activity.fuel_percentage) if activity.fuel_percentage else None,
                'alert_level': activity.alert_level,
                'breach_type': activity.breach_type,
                'is_critical': activity.is_critical,
                'timestamp': activity.timestamp.isoformat(),
                'date': activity.activity_date.isoformat(),
                'time': activity.activity_time.isoformat(),
                'notes': activity.notes,
            })
        
        logger.info(f"📊 Retrieved {len(activities_data)} activities (total: {total_count})")
        
        return JsonResponse({
            'count': len(activities_data),
            'total_count': total_count,
            'days': days,
            'activities': activities_data,
        }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Activity retrieval error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_activity_summary(request):
    """
    GET /api/v1/activities/summary/?days=7
    
    Get summary statistics of activities
    """
    try:
        days = int(request.GET.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get summary stats
        query = FleetActivity.objects.filter(timestamp__gte=start_date)
        
        total_activities = query.count()
        critical_count = query.filter(is_critical=True).count()
        
        # By category
        category_summary = {}
        for category in ['mission', 'location', 'speed', 'fuel', 'alert', 'breach', 'driver', 'maintenance', 'trail', 'cargo']:
            count = query.filter(activity_category=category).count()
            if count > 0:
                category_summary[category] = count
        
        # By type (top 10)
        type_summary = {}
        for activity in query.values('activity_type').distinct():
            activity_type = activity['activity_type']
            count = query.filter(activity_type=activity_type).count()
            if count > 0:
                type_summary[activity_type] = count
        
        # Trucks with most activities
        trucks_summary = {}
        for activity in query.filter(truck__isnull=False).values('truck__truck_identifier').distinct():
            truck_id = activity['truck__truck_identifier']
            count = query.filter(truck__truck_identifier=truck_id).count()
            if count > 0:
                trucks_summary[truck_id] = count
        
        # Drivers with most activities
        drivers_summary = {}
        for activity in query.filter(driver__isnull=False).values('driver__first_name', 'driver__last_name').distinct():
            driver_name = f"{activity['driver__first_name']} {activity['driver__last_name']}"
            count = query.filter(driver__first_name=activity['driver__first_name'], 
                               driver__last_name=activity['driver__last_name']).count()
            if count > 0:
                drivers_summary[driver_name] = count
        
        logger.info(f"📊 Activity summary: {total_activities} total, {critical_count} critical")
        
        return JsonResponse({
            'period_days': days,
            'total_activities': total_activities,
            'critical_count': critical_count,
            'by_category': category_summary,
            'by_type': type_summary,
            'by_truck': trucks_summary,
            'by_driver': drivers_summary,
        }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Activity summary error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_critical_activities(request):
    """
    GET /api/v1/activities/critical/?days=7&limit=50
    
    Get only critical activities
    """
    try:
        days = int(request.GET.get('days', 7))
        limit = int(request.GET.get('limit', 50))
        
        start_date = timezone.now() - timedelta(days=days)
        activities = FleetActivity.objects.filter(
            is_critical=True,
            timestamp__gte=start_date
        )[:limit]
        
        activities_data = []
        for activity in activities:
            activities_data.append({
                'id': str(activity.id),
                'truck_identifier': activity.truck.truck_identifier if activity.truck else None,
                'driver_name': activity.driver.get_display_name() if activity.driver else None,
                'activity_type': activity.get_activity_type_display(),
                'breach_type': activity.breach_type,
                'violation_details': activity.violation_details,
                'location': activity.display_location,
                'timestamp': activity.timestamp.isoformat(),
                'notes': activity.notes,
            })
        
        return JsonResponse({
            'count': len(activities_data),
            'critical_activities': activities_data,
        }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Critical activities error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
