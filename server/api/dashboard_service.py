"""
Dashboard Service - Aggregates data from drivers, trucks, missions for unified dashboard display
Handles performance calculations, fuel metrics, and real-time status updates
"""

from decimal import Decimal
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models_v2 import FleetDriver, FleetTruck, FleetMission, MissionStatus, DriverStatus, TruckStatus
from .osrm_service import compute_route_geometry
import math

# ============================================================
# DRIVER PERFORMANCE CALCULATION
# ============================================================

def calculate_driver_performance_points(driver_id):
    """
    Calculate driver performance points based on:
    - Each completed mission: 5 points
    - On-time delivery: 5 points (completed_at <= ETA)
    - Safe driving (no incidents): bonus points (future)
    
    Returns: int (total performance points)
    """
    driver = FleetDriver.objects.filter(id=driver_id).first()
    if not driver:
        return 0
    
    points = 0
    
    # Get all completed missions for this driver
    completed_missions = FleetMission.objects.filter(
        driver_id=driver_id,
        status=MissionStatus.COMPLETED
    )
    
    # 5 points per completed mission
    completed_count = completed_missions.count()
    points += completed_count * 5
    
    # 5 points for on-time delivery
    on_time_count = 0
    for mission in completed_missions:
        if mission.eta and mission.completed_at and mission.completed_at <= mission.eta:
            on_time_count += 1
    points += on_time_count * 5
    
    # Update driver's performance_mark
    driver.performance_mark = points
    driver.deliveries_count = completed_count
    driver.save(update_fields=['performance_mark', 'deliveries_count', 'updated_at'])
    
    return points


def recalculate_all_drivers_performance():
    """Recalculate performance for all drivers"""
    drivers = FleetDriver.objects.all()
    results = {}
    for driver in drivers:
        results[str(driver.id)] = calculate_driver_performance_points(driver.id)
    return results


# ============================================================
# MISSION DISTANCE AND PROGRESS CALCULATION
# ============================================================

def calculate_mission_distance_from_osrm(mission):
    """
    Calculate mission distance using OSRM if not already calculated
    Returns: distance in meters (int)
    """
    # If distance is already calculated, return it
    if mission.distance_total_m and mission.distance_total_m > 0:
        return int(mission.distance_total_m)
    
    # Try to compute from origin and destination
    if not mission.origin or not mission.destination:
        return 0
    
    try:
        origin_lat = mission.origin.get('lat')
        origin_lon = mission.origin.get('lon')
        dest_lat = mission.destination.get('lat')
        dest_lon = mission.destination.get('lon')
        
        if not all([origin_lat, origin_lon, dest_lat, dest_lon]):
            return 0
        
        # Call OSRM to compute route distance
        route_data = compute_route_geometry(
            origin_lat=float(origin_lat),
            origin_lng=float(origin_lon),
            dest_lat=float(dest_lat),
            dest_lng=float(dest_lon)
        )
        
        if route_data and route_data.get('distance'):
            distance_m = int(route_data['distance'])
            # Update mission with calculated distance
            mission.distance_total_m = distance_m
            mission.distance_remaining_m = distance_m
            mission.save(update_fields=['distance_total_m', 'distance_remaining_m', 'updated_at'])
            return distance_m
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating distance from OSRM for mission {mission.id}: {e}")
    
    return 0


def calculate_mission_progress(mission):
    """
    Calculate mission progress percentage based on current location
    Progress = (Distance traveled / Total distance) * 100
    
    Returns: float (0-100)
    """
    if not mission.distance_total_m or mission.distance_total_m == 0:
        return 0.0
    
    # If mission not started, progress is 0
    if mission.status == MissionStatus.PLANNED or mission.status == MissionStatus.ASSIGNED:
        return 0.0
    
    # If mission completed, progress is 100
    if mission.status == MissionStatus.COMPLETED:
        return 100.0
    
    # Calculate progress based on current location
    if not mission.current_location or not mission.origin or not mission.destination:
        # If no current location but mission is enroute, assume some progress
        if mission.status in [MissionStatus.ENROUTE, MissionStatus.PAUSED]:
            return 50.0
        return 0.0
    
    try:
        current_lat = mission.current_location.get('lat')
        current_lon = mission.current_location.get('lon')
        origin_lat = mission.origin.get('lat')
        origin_lon = mission.origin.get('lon')
        dest_lat = mission.destination.get('lat')
        dest_lon = mission.destination.get('lon')
        
        if not all([current_lat, current_lon, origin_lat, origin_lon, dest_lat, dest_lon]):
            # If any location data missing, use simple heuristic
            return 50.0 if mission.status == MissionStatus.ENROUTE else 0.0
        
        # Calculate distance from current location to destination
        # using Haversine formula (fast approximation)
        remaining_route = compute_route_geometry(
            origin_lat=float(current_lat),
            origin_lng=float(current_lon),
            dest_lat=float(dest_lat),
            dest_lng=float(dest_lon)
        )
        
        if remaining_route and remaining_route.get('distance'):
            remaining_distance = remaining_route['distance']
            progress = ((float(mission.distance_total_m) - remaining_distance) / float(mission.distance_total_m)) * 100
            progress = max(0, min(100, progress))  # Clamp between 0-100
            return float(progress)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating progress for mission {mission.id}: {e}")
        return 50.0 if mission.status == MissionStatus.ENROUTE else 0.0
    
    return 50.0 if mission.status == MissionStatus.ENROUTE else 0.0


# ============================================================
# TRUCK DATA AGGREGATION FROM MISSIONS
# ============================================================

def get_truck_location_from_missions(truck_id):
    """
    Get truck's current location from the latest mission
    Returns: {'lat': float, 'lon': float} or None
    """
    latest_mission = FleetMission.objects.filter(
        truck_id=truck_id
    ).order_by('-updated_at').first()
    
    if latest_mission and latest_mission.current_location:
        return latest_mission.current_location
    return None


def get_truck_status_from_missions(truck_id):
    """
    Get truck's status based on active missions
    Returns: str (status from TruckStatus.choices)
    
    Logic:
    - If has ENROUTE mission: ENROUTE
    - If has PAUSED mission: ENROUTE (paused)
    - Otherwise: IDLE
    """
    active_mission = FleetMission.objects.filter(
        truck_id=truck_id,
        status__in=[MissionStatus.ENROUTE, MissionStatus.PAUSED]
    ).order_by('-updated_at').first()
    
    if active_mission:
        return TruckStatus.ENROUTE
    return TruckStatus.IDLE


def calculate_truck_fuel_consumption(truck_id):
    """
    Calculate fuel consumed based on missions distance and fuel consumption rate
    
    Formula: (Total Distance in km) * (Fuel Consumption Rate L/100km) / 100
    
    Recommendation: 
    - Use 8 L/100km as default (typical for medium trucks)
    - Can be calibrated per truck based on real data
    - Can be adjusted based on truck make/model
    
    Returns: {
        'fuel_consumed_liters': float,
        'distance_travelled_km': float,
        'fuel_rate_per_100km': float,
        'estimated_consumption': float
    }
    """
    truck = FleetTruck.objects.filter(id=truck_id).first()
    if not truck:
        return {
            'fuel_consumed_liters': 0,
            'distance_travelled_km': 0,
            'fuel_rate_per_100km': 8.0,
            'estimated_consumption': 0
        }
    
    # Get all missions for this truck (except cancelled)
    missions = FleetMission.objects.filter(
        truck_id=truck_id
    ).exclude(status=MissionStatus.CANCELLED)
    
    # Ensure all missions have distance calculated
    total_distance_m = 0
    for mission in missions:
        distance = calculate_mission_distance_from_osrm(mission)
        total_distance_m += distance
    
    total_distance_km = float(total_distance_m) / 1000 if total_distance_m else 0
    
    # Default fuel consumption rate: 8 L/100km (can be customized per truck)
    # This is typical for medium commercial trucks
    fuel_rate = 8.0  # L/100km
    
    # Calculate estimated fuel consumption
    estimated_fuel = (total_distance_km * fuel_rate) / 100
    
    # Update truck's fuel metrics
    truck.kilometers_travelled_km = Decimal(str(total_distance_km))
    truck.fuel_consumed_liters = Decimal(str(estimated_fuel))
    truck.save(update_fields=['kilometers_travelled_km', 'fuel_consumed_liters', 'updated_at'])
    
    return {
        'fuel_consumed_liters': estimated_fuel,
        'distance_travelled_km': total_distance_km,
        'fuel_rate_per_100km': fuel_rate,
        'estimated_consumption': estimated_fuel
    }


def sync_truck_data_from_missions(truck_id):
    """
    Sync truck data from missions table:
    - Location (current_location)
    - Status (from active missions)
    - Fuel consumption (calculated)
    - Kilometers travelled
    """
    truck = FleetTruck.objects.filter(id=truck_id).first()
    if not truck:
        return None
    
    # Get location from latest mission
    location = get_truck_location_from_missions(truck_id)
    if location:
        truck.last_latitude = Decimal(str(location.get('lat', 0)))
        truck.last_longitude = Decimal(str(location.get('lon', 0)))
        truck.last_location_ts = timezone.now()
    
    # Get status from active missions
    status = get_truck_status_from_missions(truck_id)
    truck.status = status
    
    # Calculate fuel consumption
    fuel_data = calculate_truck_fuel_consumption(truck_id)
    
    truck.save()
    
    return {
        'truck_id': str(truck.id),
        'truck_identifier': truck.truck_identifier,
        'location': location,
        'status': status,
        'fuel_metrics': fuel_data
    }


# ============================================================
# UNIFIED DASHBOARD DATA
# ============================================================

def get_dashboard_summary():
    """
    Get comprehensive dashboard summary for main dashboard
    Aggregates data from drivers, trucks, and missions tables
    """
    
    # Driver metrics
    total_drivers = FleetDriver.objects.filter(status=DriverStatus.ACTIVE).count()
    active_drivers = FleetDriver.objects.filter(
        status=DriverStatus.ACTIVE,
        on_duty=True
    ).count()
    avg_performance = FleetDriver.objects.filter(
        status=DriverStatus.ACTIVE
    ).aggregate(avg=Avg('performance_mark'))['avg'] or 0
    
    # Truck metrics
    total_trucks = FleetTruck.objects.count()
    active_trucks = FleetTruck.objects.filter(status=TruckStatus.ENROUTE).count()
    idle_trucks = FleetTruck.objects.filter(status=TruckStatus.IDLE).count()
    
    # Mission metrics
    total_missions = FleetMission.objects.count()
    completed_missions = FleetMission.objects.filter(status=MissionStatus.COMPLETED).count()
    enroute_missions = FleetMission.objects.filter(status=MissionStatus.ENROUTE).count()
    on_time_deliveries = FleetMission.objects.filter(
        status=MissionStatus.COMPLETED
    ).exclude(eta=None, completed_at=None).filter(
        completed_at__lte=timezone.now()  # This should compare with ETA properly
    ).count()
    
    # Calculate on-time percentage
    on_time_rate = (on_time_deliveries / completed_missions * 100) if completed_missions > 0 else 0
    
    # Total distance and fuel metrics
    total_distance_m = FleetMission.objects.filter(
        status=MissionStatus.COMPLETED
    ).aggregate(total=Sum('distance_total_m'))['total'] or 0
    total_distance_km = float(total_distance_m) / 1000
    
    # Estimated total fuel consumption (8 L/100km)
    total_fuel_consumed = (total_distance_km * 8) / 100
    
    return {
        'timestamp': timezone.now().isoformat(),
        'drivers': {
            'total': total_drivers,
            'active': active_drivers,
            'avg_performance_points': float(avg_performance),
        },
        'trucks': {
            'total': total_trucks,
            'active': active_trucks,
            'idle': idle_trucks,
        },
        'missions': {
            'total': total_missions,
            'completed': completed_missions,
            'enroute': enroute_missions,
            'on_time_deliveries': on_time_deliveries,
            'on_time_rate_percent': float(on_time_rate),
        },
        'metrics': {
            'total_distance_km': total_distance_km,
            'total_fuel_consumed_liters': total_fuel_consumed,
            'avg_fuel_consumption_per_100km': 8.0,
        }
    }


def get_drivers_with_performance():
    """Get all drivers with calculated performance points"""
    drivers = FleetDriver.objects.filter(status=DriverStatus.ACTIVE)
    result = []
    for driver in drivers:
        # Recalculate to ensure fresh data
        performance_points = calculate_driver_performance_points(driver.id)
        result.append({
            'id': str(driver.id),
            'name': driver.get_display_name(),
            'email': driver.email,
            'phone': driver.phone,
            'license_number': driver.license_number,
            'performance_points': performance_points,
            'deliveries_count': driver.deliveries_count,
            'status': driver.status,
            'on_duty': driver.on_duty,
            'hire_date': driver.hire_date.isoformat() if driver.hire_date else None,
        })
    return result


def get_trucks_with_mission_data():
    """Get all trucks with data synced from missions"""
    trucks = FleetTruck.objects.all()
    result = []
    for truck in trucks:
        # Sync data from missions
        sync_truck_data_from_missions(truck.id)
        
        # Get current location and status
        location = get_truck_location_from_missions(truck.id)
        status = get_truck_status_from_missions(truck.id)
        fuel_data = calculate_truck_fuel_consumption(truck.id)
        
        result.append({
            'id': str(truck.id),
            'truck_identifier': truck.truck_identifier,
            'plate': truck.plate,
            'make': truck.make,
            'model': truck.model,
            'status': str(status) if status else 'IDLE',  # Convert enum to string
            'location': location,
            'latitude': float(truck.last_latitude) if truck.last_latitude else None,
            'longitude': float(truck.last_longitude) if truck.last_longitude else None,
            'fuel_consumed_liters': float(fuel_data['fuel_consumed_liters']),
            'distance_travelled_km': float(fuel_data['distance_travelled_km']),
            'fuel_rate_per_100km': fuel_data['fuel_rate_per_100km'],
            'fuel_capacity_liters': float(truck.fuel_capacity_liters),
            'fuel_percent': (float(fuel_data['fuel_consumed_liters']) / float(truck.fuel_capacity_liters) * 100) if truck.fuel_capacity_liters else 0,
            'assigned_driver': truck.assigned_driver.get_display_name() if truck.assigned_driver else None,
        })
    return result


def get_missions_with_details():
    """Get all missions with driver and truck details"""
    missions = FleetMission.objects.select_related('driver', 'truck').all()
    result = []
    for mission in missions:
        # Calculate distance using OSRM if not already set
        distance_m = calculate_mission_distance_from_osrm(mission)
        
        # Calculate progress based on current location
        progress_pct = calculate_mission_progress(mission)
        
        result.append({
            'id': str(mission.id),
            'mission_number': mission.mission_number,
            'truck_identifier': mission.truck.truck_identifier if mission.truck else 'Unassigned',
            'driver_name': mission.driver.get_display_name() if mission.driver else 'Unassigned',
            'status': str(mission.status).upper() if mission.status else 'PLANNED',  # Convert to uppercase string
            'priority': mission.priority,
            'progress_pct': float(progress_pct),  # Match frontend field name
            'distance_total_m': float(distance_m) if distance_m else 0,  # Keep in meters for frontend
            'stops_detail': mission.stops or [],  # For stops count
            'origin': mission.origin,
            'destination': mission.destination,
            'current_location': mission.current_location,
            'eta': mission.eta.isoformat() if mission.eta else None,
            'created_at': mission.created_at.isoformat(),
            'started_at': mission.started_at.isoformat() if mission.started_at else None,
            'completed_at': mission.completed_at.isoformat() if mission.completed_at else None,
            'mission_date': mission.mission_date.isoformat() if mission.mission_date else None,
        })
    return result
