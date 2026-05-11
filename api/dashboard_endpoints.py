"""
Dashboard API Endpoints
Provides unified dashboard data with aggregated metrics from drivers, trucks, and missions
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import logging

from .dashboard_service import (
    get_dashboard_summary,
    get_drivers_with_performance,
    get_trucks_with_mission_data,
    get_missions_with_details,
    recalculate_all_drivers_performance,
    sync_truck_data_from_missions
)
from .osrm_service import compute_route_geometry

logger = logging.getLogger(__name__)


@api_view(['GET'])
def dashboard_summary(request):
    """
    GET /api/v1/dashboard/summary/
    
    Returns unified dashboard summary with:
    - Active drivers, trucks, missions
    - Performance metrics
    - On-time delivery rates
    - Total distance and fuel metrics
    """
    try:
        data = get_dashboard_summary()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Error getting dashboard summary: {str(e)}')
        return Response(
            {'error': 'Failed to get dashboard summary'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def drivers_list_with_performance(request):
    """
    GET /api/v1/dashboard/drivers/
    
    Returns list of drivers with calculated performance points:
    - Performance points (from completed missions + on-time bonuses)
    - Deliveries count
    - Status and duty information
    """
    try:
        data = get_drivers_with_performance()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Error getting drivers performance: {str(e)}')
        return Response(
            {'error': 'Failed to get drivers performance'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def trucks_list_with_mission_data(request):
    """
    GET /api/v1/dashboard/trucks/
    
    Returns list of trucks with synced mission data:
    - Current location (from latest mission)
    - Status (from active missions)
    - Fuel consumption (calculated from distance)
    - Distance travelled (from completed missions)
    """
    try:
        data = get_trucks_with_mission_data()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Error getting trucks mission data: {str(e)}')
        return Response(
            {'error': 'Failed to get trucks mission data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def missions_list_with_details(request):
    """
    GET /api/v1/dashboard/missions/
    
    Returns list of missions with full details:
    - Driver and truck information
    - Progress and distance metrics
    - Origin, destination, and current location
    - ETA and completion status
    """
    try:
        data = get_missions_with_details()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Error getting missions details: {str(e)}')
        return Response(
            {'error': 'Failed to get missions details'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def recalculate_performance(request):
    """
    POST /api/v1/dashboard/recalculate-performance/
    
    Recalculates performance points for all drivers
    Should be called periodically or after mission completion
    
    Returns: Dict with driver_id -> performance_points mapping
    """
    try:
        results = recalculate_all_drivers_performance()
        return Response({
            'status': 'success',
            'message': 'Performance recalculated for all drivers',
            'results': results
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Error recalculating performance: {str(e)}')
        return Response(
            {'error': 'Failed to recalculate performance'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def sync_truck_data(request):
    """
    POST /api/v1/dashboard/sync-truck-data/
    
    Syncs truck data from missions table:
    - Location, status, fuel consumption
    Can be called for all trucks or specific truck_id
    
    Request body (optional): {'truck_id': 'uuid'}
    """
    try:
        truck_id = request.data.get('truck_id') if request.data else None
        
        if truck_id:
            result = sync_truck_data_from_missions(truck_id)
            return Response({
                'status': 'success',
                'message': f'Synced truck data for {truck_id}',
                'result': result
            }, status=status.HTTP_200_OK)
        else:
            # Sync all trucks
            from .models_v2 import FleetTruck
            trucks = FleetTruck.objects.all()
            results = []
            for truck in trucks:
                result = sync_truck_data_from_missions(truck.id)
                results.append(result)
            
            return Response({
                'status': 'success',
                'message': f'Synced data for {len(results)} trucks',
                'results': results
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Error syncing truck data: {str(e)}')
        return Response(
            {'error': 'Failed to sync truck data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def mission_route_geometry(request, mission_id):
    """
    GET /api/v1/dashboard/missions/{mission_id}/route-geometry/
    
    Returns OSRM-based route geometry for a mission following actual roads
    Route goes from current_location (if available) or origin → destination
    This shows where the truck has been and where it's going
    
    Returns: {
        'geometry': GeoJSON LineString geometry,
        'distance': distance in meters,
        'duration': duration in seconds,
    }
    """
    try:
        from .models_v2 import FleetMission
        
        mission = FleetMission.objects.filter(id=mission_id).first()
        if not mission:
            return Response(
                {'error': 'Mission not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prefer current_location as start point (shows where truck has been)
        # Falls back to origin if current_location not available
        if mission.current_location:
            start_lat = mission.current_location.get('lat')
            start_lon = mission.current_location.get('lon')
        elif mission.origin:
            start_lat = mission.origin.get('lat')
            start_lon = mission.origin.get('lon')
        else:
            return Response(
                {'error': 'Mission missing origin and current location'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get destination coordinates
        if not mission.destination:
            return Response(
                {'error': 'Mission missing destination'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dest_lat = mission.destination.get('lat')
        dest_lon = mission.destination.get('lon')
        
        if not all([start_lat, start_lon, dest_lat, dest_lon]):
            return Response(
                {'error': 'Invalid coordinate data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Compute route using OSRM (without waypoints for faster response)
        logger.info(f'🛣️ Computing route for mission {mission.mission_number} from current/origin to destination')
        route_data = compute_route_geometry(
            origin_lat=float(start_lat),
            origin_lng=float(start_lon),
            dest_lat=float(dest_lat),
            dest_lng=float(dest_lon),
            waypoints=None  # Skip waypoints for performance
        )
        
        if not route_data:
            logger.warning(f'❌ Could not compute route for mission {mission.mission_number}')
            return Response(
                {'error': 'Could not compute route geometry'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return route geometry for frontend rendering
        logger.info(f'✅ Route computed: {route_data.get("distance", 0)/1000:.2f}km')
        return Response({
            'mission_id': str(mission.id),
            'mission_number': mission.mission_number,
            'geometry': route_data['geometry'],
            'distance': route_data.get('distance', 0),
            'duration': route_data.get('duration', 0),
            'start_type': 'current_location' if mission.current_location else 'origin',
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f'Error computing mission route geometry: {str(e)}')
        return Response(
            {'error': f'Failed to compute route geometry: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
