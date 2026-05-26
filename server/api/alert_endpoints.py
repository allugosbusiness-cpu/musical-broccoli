"""
Smart Alert System
- Overspeed detection (>100 km/h)
- Delay detection (stopped >5 min)
- Driver-crafted alerts
- ALL alerts logged to FleetActivity (activity trail)
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

from .models import Alert, FleetTruck, FleetDriver, FleetMission, TruckLocation, FleetActivity

logger = logging.getLogger(__name__)

OVERSPEED_THRESHOLD = 100
DELAY_MINUTES = 5
DELAY_SPEED_THRESHOLD = 3


def log_alert_to_activity(truck, driver, mission, alert_type, message, latitude, longitude, speed, severity='high'):
    """Log any alert to the FleetActivity table for the audit trail view."""
    try:
        category_map = {
            'overspeed': 'speed',
            'delayed': 'trail',
            'driver_alert': 'driver',
            'off_route': 'breach',
            'maintenance': 'maintenance',
        }
        category = category_map.get(alert_type, 'alert')
        
        FleetActivity.objects.create(
            fleet_id=truck.fleet_id if truck else (driver.fleet_id if driver else None),
            truck=truck,
            driver=driver,
            mission=mission,
            activity_type='alert',
            activity_category=category,
            location_lat=latitude,
            location_lon=longitude,
            speed_kmh=speed,
            alert_level=severity,
            breach_type='speeding' if alert_type == 'overspeed' else alert_type,
            violation_details=message[:500],
            notes=f'{alert_type}: {message[:200]}',
            is_critical=(severity in ['high', 'critical']),
            timestamp=timezone.now(),
        )
    except Exception as e:
        logger.warning(f'Failed to log alert to activity trail: {e}')


@csrf_exempt
@require_http_methods(["POST"])
def check_and_create_alerts(request):
    """POST /api/v1/alerts/check/
    
    Called after each location update. Checks:
    1. Overspeeding (speed > 100 km/h)
    2. Delayed (stopped > 5 minutes)
    Returns active alerts.
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
        truck = None; driver = None; mission = None
        
        if truck_id:
            try: truck = FleetTruck.objects.get(id=truck_id)
            except FleetTruck.DoesNotExist: pass
        if driver_id:
            try: driver = FleetDriver.objects.get(id=driver_id)
            except FleetDriver.DoesNotExist: pass
        if mission_id:
            try: mission = FleetMission.objects.get(id=mission_id)
            except FleetMission.DoesNotExist: pass
        
        # === 1. OVERSPEED ===
        if current_speed > OVERSPEED_THRESHOLD:
            existing = Alert.objects.filter(alert_type='overspeed', is_resolved=False)
            if truck: existing = existing.filter(truck=truck)
            if not existing.exists():
                truck_name = truck.truck_identifier if truck else "Truck"
                msg = f'⚠️ OVERSPEED: {truck_name} at {current_speed:.0f} km/h (limit: {OVERSPEED_THRESHOLD})'
                alert = Alert.objects.create(
                    id=uuid.uuid4(), truck=truck, driver=driver,
                    alert_type='overspeed', severity='high', message=msg,
                    location_lat=latitude, location_lon=longitude, speed_kmh=current_speed,
                )
                alerts_created.append({'id': str(alert.id), 'type': 'overspeed', 'severity': 'high', 'message': msg, 'speed': current_speed})
                # Log to activity trail
                log_alert_to_activity(truck, driver, mission, 'overspeed', msg, latitude, longitude, current_speed, 'high')
                logger.warning(f'🚨 OVERSPEED: {truck_name} at {current_speed} km/h')
        
        # === 2. DELAY ===
        if current_speed < DELAY_SPEED_THRESHOLD and truck:
            recent = TruckLocation.objects.filter(truck=truck).order_by('-timestamp')[:20]
            if recent.count() >= 5:
                stopped_count = sum(1 for loc in recent if float(loc.speed) < DELAY_SPEED_THRESHOLD)
                if stopped_count >= 5:
                    first_stopped = list(recent)[-1]
                    duration = (timezone.now() - first_stopped.timestamp).total_seconds() / 60
                    if duration >= DELAY_MINUTES:
                        existing = Alert.objects.filter(alert_type='delayed', is_resolved=False, truck=truck)
                        if not existing.exists():
                            mi = f" on mission {mission.mission_number}" if mission else ""
                            msg = f'⏰ DELAYED: {truck.truck_identifier} stopped {duration:.0f} min{mi}'
                            alert = Alert.objects.create(
                                id=uuid.uuid4(), truck=truck, driver=driver, mission=mission,
                                alert_type='delayed', severity='medium', message=msg,
                                location_lat=latitude, location_lon=longitude, speed_kmh=current_speed,
                            )
                            alerts_created.append({'id': str(alert.id), 'type': 'delayed', 'severity': 'medium', 'message': msg, 'stopped_minutes': round(duration, 1)})
                            log_alert_to_activity(truck, driver, mission, 'delayed', msg, latitude, longitude, current_speed, 'medium')
                            logger.warning(f'⏰ DELAY: {truck.truck_identifier} stopped {duration:.0f} min')
        
        # Active alerts for this truck/driver
        active = Alert.objects.filter(is_resolved=False).order_by('-created_at')[:20]
        if truck: active = active.filter(Q(truck=truck) | Q(truck__isnull=True))
        active_alerts = [{
            'id': str(a.id), 'type': a.alert_type, 'severity': a.severity,
            'message': a.message, 'speed_kmh': float(a.speed_kmh) if a.speed_kmh else None,
            'created_at': a.created_at.isoformat(), 'is_resolved': a.is_resolved,
        } for a in active]
        
        return JsonResponse({'success': True, 'alerts_created': alerts_created, 'active_alerts': active_alerts, 'alert_count': len(active_alerts)})
    except Exception as e:
        logger.error(f'Alert check error: {str(e)}')
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def driver_send_alert(request):
    """POST /api/v1/alerts/driver-send/
    
    Driver sends custom alert to fleet manager. Also logged to activity trail.
    """
    try:
        data = json.loads(request.body) if request.body else {}
        driver_id = data.get('driver_id'); truck_id = data.get('truck_id')
        message = data.get('message', '').strip()
        alert_category = data.get('alert_category', 'other')
        latitude = float(data.get('latitude', 0)); longitude = float(data.get('longitude', 0))
        speed = float(data.get('speed', 0))
        
        if not message: return JsonResponse({'error': 'Message is required'}, status=400)
        if len(message) < 5: return JsonResponse({'error': 'Message must be at least 5 characters'}, status=400)
        if len(message) > 500: return JsonResponse({'error': 'Message too long (max 500 chars)'}, status=400)
        
        driver = None; truck = None
        if driver_id:
            try: driver = FleetDriver.objects.get(id=driver_id)
            except: pass
        if truck_id:
            try: truck = FleetTruck.objects.get(id=truck_id)
            except: pass
        mission = FleetMission.objects.filter(driver=driver, status__in=['enroute', 'in_progress']).first() if driver else None
        
        driver_name = driver.get_display_name() if driver else "Unknown Driver"
        truck_name = truck.truck_identifier if truck else "Unknown Truck"
        msg = f'📢 DRIVER ({driver_name}/{truck_name}): {message}'
        
        alert = Alert.objects.create(
            id=uuid.uuid4(), truck=truck, driver=driver, mission=mission,
            alert_type='driver_alert', severity='high', message=msg,
            location_lat=latitude, location_lon=longitude, speed_kmh=speed,
        )
        
        # Log to activity trail
        log_alert_to_activity(truck, driver, mission, 'driver_alert', msg, latitude, longitude, speed, 'high')
        
        logger.info(f'📢 Driver alert from {driver_name}: {message}')
        return JsonResponse({'success': True, 'alert_id': str(alert.id), 'message': 'Alert sent to fleet manager',
            'alert': {'id': str(alert.id), 'type': alert.alert_type, 'severity': alert.severity, 'message': alert.message, 'created_at': alert.created_at.isoformat()}}, status=201)
    except Exception as e:
        logger.error(f'Driver alert error: {str(e)}')
        return JsonResponse({'error': str(e)}, status=400)