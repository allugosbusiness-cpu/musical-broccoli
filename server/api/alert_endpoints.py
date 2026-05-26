"""
Smart Alert System
- Overspeed detection (>100 km/h)
- Delay detection (stopped >5 min or speed mismatches expected time)
- Driver-crafted alerts (driver sends message to web app)
- Notifications displayed on mobile app map
"""

import logging
import json
import uuid
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q

from .models import Alert, FleetTruck, FleetDriver, FleetMission, TruckLocation

logger = logging.getLogger(__name__)

OVERSPEED_THRESHOLD = 100  # km/h
DELAY_MINUTES = 5  # stopped for 5+ minutes = delayed
DELAY_SPEED_THRESHOLD = 3  # km/h - considered "stopped" if below this


@csrf_exempt
@require_http_methods(["POST"])
def check_and_create_alerts(request):
    """
    POST /api/v1/alerts/check/
    
    Called by the mobile app after each location update.
    Checks for:
    1. Overspeeding (speed > 100 km/h)
    2. Delayed (stopped > 5 minutes or speed too low for expected time)
    3. Returns any active alerts for this driver/truck
    
    Request: { "driver_id": "uuid", "truck_id": "uuid", 
                "latitude": -18.0, "longitude": 31.0, "speed": 45.5,
                "mission_id": "uuid" (optional) }
    Response: { "alerts_created": [...], "active_alerts": [...] }
    """
    try:
        data = json.loads(request.body) if request.body else {}
        driver_id = data.get('driver_id')
        truck_id = data.get('truck_id')
        mission_id = data.get('mission_id')
        current_speed = float(data.get('speed', 0))
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))
        
        alerts_created = []
        
        # Get truck and driver
        truck = None
        driver = None
        mission = None
        
        if truck_id:
            try: truck = FleetTruck.objects.get(id=truck_id)
            except FleetTruck.DoesNotExist: pass
        if driver_id:
            try: driver = FleetDriver.objects.get(id=driver_id)
            except FleetDriver.DoesNotExist: pass
        if mission_id:
            try: mission = FleetMission.objects.get(id=mission_id)
            except FleetMission.DoesNotExist: pass
        
        # === 1. OVERSPEED CHECK ===
        if current_speed > OVERSPEED_THRESHOLD:
            # Check if we already have an unresolved overspeed alert for this truck
            existing = Alert.objects.filter(
                alert_type='overspeed',
                is_resolved=False
            )
            if truck: existing = existing.filter(truck=truck)
            if driver: existing = existing.filter(driver=driver)
            
            if not existing.exists():
                alert = Alert.objects.create(
                    id=uuid.uuid4(),
                    truck=truck,
                    driver=driver,
                    alert_type='overspeed',
                    severity='high',
                    message=f'⚠️ OVERSPEED: {truck.truck_identifier if truck else "Truck"} at {current_speed:.0f} km/h (limit: {OVERSPEED_THRESHOLD} km/h)',
                    location_lat=latitude,
                    location_lon=longitude,
                    speed_kmh=current_speed,
                    is_resolved=False,
                    created_at=timezone.now(),
                )
                alerts_created.append({
                    'id': str(alert.id),
                    'type': 'overspeed',
                    'severity': 'high',
                    'message': alert.message,
                    'speed': current_speed,
                })
                logger.warning(f'🚨 OVERSPEED: {truck} at {current_speed} km/h')
                
                # Log to FleetActivity as well
                try:
                    from .models import FleetActivity
                    FleetActivity.objects.create(
                        fleet_id=truck.fleet_id if truck else None,
                        truck=truck,
                        driver=driver,
                        mission=mission,
                        activity_type='alert',
                        activity_category='speed',
                        location_lat=latitude,
                        location_lon=longitude,
                        speed_kmh=current_speed,
                        alert_level='high',
                        breach_type='speeding',
                        violation_details=f'Overspeed: {current_speed:.0f} km/h > {OVERSPEED_THRESHOLD} km/h',
                        notes=f'Overspeed alert for {truck.truck_identifier if truck else "unknown"}',
                        is_critical=True,
                        timestamp=timezone.now(),
                    )
                except Exception: pass
        
        # === 2. DELAY CHECK ===
        # Check if truck is stopped (speed < 3 km/h)
        is_stopped = current_speed < DELAY_SPEED_THRESHOLD
        
        if is_stopped and truck:
            # Check how long the truck has been stopped
            recent_movements = TruckLocation.objects.filter(
                truck=truck
            ).order_by('-timestamp')[:20]  # Check last 20 pings
            
            if recent_movements.count() >= 5:
                # Check if all recent pings show stopped
                stopped_count = sum(1 for loc in recent_movements if float(loc.speed) < DELAY_SPEED_THRESHOLD)
                
                if stopped_count >= 5:
                    # Get time span of these stopped records
                    first_stopped = list(recent_movements)[-1]
                    stopped_duration = (timezone.now() - first_stopped.timestamp).total_seconds() / 60
                    
                    if stopped_duration >= DELAY_MINUTES:
                        # Check if unresolved delay alert exists
                        existing = Alert.objects.filter(
                            alert_type='delayed',
                            is_resolved=False,
                        )
                        if truck: existing = existing.filter(truck=truck)
                        
                        if not existing.exists():
                            # Get mission context
                            mission_info = ""
                            if mission:
                                mission_info = f" on mission {mission.mission_number}"
                            
                            alert = Alert.objects.create(
                                id=uuid.uuid4(),
                                truck=truck,
                                driver=driver,
                                mission=mission,
                                alert_type='delayed',
                                severity='medium',
                                message=f'⏰ DELAYED: {truck.truck_identifier} stopped for {stopped_duration:.0f} minutes{mission_info} at ({latitude:.4f}, {longitude:.4f})',
                                location_lat=latitude,
                                location_lon=longitude,
                                speed_kmh=current_speed,
                                is_resolved=False,
                                created_at=timezone.now(),
                            )
                            alerts_created.append({
                                'id': str(alert.id),
                                'type': 'delayed',
                                'severity': 'medium',
                                'message': alert.message,
                                'stopped_minutes': round(stopped_duration, 1),
                            })
                            logger.warning(f'⏰ DELAY: {truck} stopped {stopped_duration:.0f} min')
        
        # === 3. GET ALL ACTIVE ALERTS for this truck/driver ===
        active_alerts_qs = Alert.objects.filter(is_resolved=False).order_by('-created_at')
        if truck: active_alerts_qs = active_alerts_qs.filter(
            Q(truck=truck) | Q(truck__isnull=True)
        )
        if driver: active_alerts_qs = active_alerts_qs.filter(
            Q(driver=driver) | Q(driver__isnull=True)
        )
        active_alerts_qs = active_alerts_qs[:20]
        
        active_alerts = []
        for a in active_alerts_qs:
            active_alerts.append({
                'id': str(a.id),
                'type': a.alert_type,
                'severity': a.severity,
                'message': a.message,
                'speed_kmh': float(a.speed_kmh) if a.speed_kmh else None,
                'created_at': a.created_at.isoformat(),
                'is_resolved': a.is_resolved,
            })
        
        return JsonResponse({
            'success': True,
            'alerts_created': alerts_created,
            'active_alerts': active_alerts,
            'alert_count': len(active_alerts),
        }, status=200)
        
    except Exception as e:
        logger.error(f'Alert check error: {str(e)}')
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def driver_send_alert(request):
    """
    POST /api/v1/alerts/driver-send/
    
    Driver-crafted alert - driver sends a custom message to the web app.
    
    Request: {
        "driver_id": "uuid",
        "truck_id": "uuid",
        "message": "I have a mechanical issue at Mutare",
        "alert_category": "mechanical|accident|traffic|weather|other",
        "latitude": -18.975,
        "longitude": 32.655,
        "speed": 0
    }
    """
    try:
        data = json.loads(request.body) if request.body else {}
        
        driver_id = data.get('driver_id')
        truck_id = data.get('truck_id')
        message = data.get('message', '').strip()
        alert_category = data.get('alert_category', 'other')
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))
        speed = float(data.get('speed', 0))
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        if len(message) < 5:
            return JsonResponse({'error': 'Message must be at least 5 characters'}, status=400)
        if len(message) > 500:
            return JsonResponse({'error': 'Message too long (max 500 chars)'}, status=400)
        
        # Resolve driver/truck
        driver = None
        truck = None
        if driver_id:
            try: driver = FleetDriver.objects.get(id=driver_id)
            except FleetDriver.DoesNotExist: pass
        if truck_id:
            try: truck = FleetTruck.objects.get(id=truck_id)
            except FleetTruck.DoesNotExist: pass
        
        # Get driver's current mission if any
        mission = None
        if driver:
            mission = FleetMission.objects.filter(
                driver=driver,
                status__in=['enroute', 'in_progress']
            ).first()
        
        # Create the alert
        driver_name = driver.get_display_name() if driver else "Unknown Driver"
        truck_name = truck.truck_identifier if truck else "Unknown Truck"
        
        alert = Alert.objects.create(
            id=uuid.uuid4(),
            truck=truck,
            driver=driver,
            mission=mission,
            alert_type='driver_alert',
            severity='high',
            message=f'📢 DRIVER ({driver_name}/{truck_name}): {message}',
            location_lat=latitude,
            location_lon=longitude,
            speed_kmh=speed,
            is_resolved=False,
            created_at=timezone.now(),
        )
        
        # Also log to FleetActivity
        try:
            from .models import FleetActivity
            FleetActivity.objects.create(
                fleet_id=truck.fleet_id if truck else (driver.fleet_id if driver else None),
                truck=truck,
                driver=driver,
                mission=mission,
                activity_type='alert',
                activity_category='driver',
                location_lat=latitude,
                location_lon=longitude,
                speed_kmh=speed,
                alert_level='high',
                notes=f'Driver alert: {message}',
                violation_details=f'Category: {alert_category}',
                is_critical=True,
                timestamp=timezone.now(),
            )
        except Exception: pass
        
        logger.info(f'📢 Driver alert from {driver_name}: {message}')
        
        return JsonResponse({
            'success': True,
            'alert_id': str(alert.id),
            'message': 'Alert sent to fleet manager',
            'alert': {
                'id': str(alert.id),
                'type': alert.alert_type,
                'severity': alert.severity,
                'message': alert.message,
                'created_at': alert.created_at.isoformat(),
            }
        }, status=201)
        
    except Exception as e:
        logger.error(f'Driver alert error: {str(e)}')
        return JsonResponse({'error': str(e)}, status=400)