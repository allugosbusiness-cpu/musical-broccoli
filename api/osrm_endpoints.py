"""
OSRM Distance Calculation Endpoints
Provides real road distance calculations using OpenStreetMap Routing Machine (OSRM)
"""

import requests
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"


@api_view(['POST'])
def calculate_distance(request):
    """
    Calculate road distance between two points using OSRM.
    
    Request body:
    {
        "origin": {"lat": float, "lon": float},
        "destination": {"lat": float, "lon": float}
    }
    
    Response:
    {
        "distance_meters": int,
        "distance_km": float,
        "duration_seconds": int,
        "duration_minutes": float
    }
    """
    try:
        data = request.data
        
        origin = data.get('origin')
        destination = data.get('destination')
        
        if not origin or not destination:
            return Response(
                {'error': 'origin and destination are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        origin_lat = origin.get('lat')
        origin_lon = origin.get('lon')
        dest_lat = destination.get('lat')
        dest_lon = destination.get('lon')
        
        if not all([origin_lat, origin_lon, dest_lat, dest_lon]):
            return Response(
                {'error': 'Invalid coordinates'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OSRM uses lon,lat format
        coords = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        url = f"{OSRM_BASE}/{coords}"
        
        params = {
            "overview": "false",
            "geometries": "geojson",
            "steps": "false",
            "annotations": "distance,duration"
        }
        
        logger.info(f"🛣️ Calculating OSRM distance: {url}")
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        osrm_data = response.json()
        
        if osrm_data.get("code") != "Ok":
            logger.error(f"❌ OSRM error: {osrm_data.get('code')}")
            # Fallback: return Haversine distance
            haversine_dist = calculate_haversine(origin_lat, origin_lon, dest_lat, dest_lon)
            return Response({
                "distance_meters": int(haversine_dist),
                "distance_km": round(haversine_dist / 1000, 2),
                "duration_seconds": 0,
                "duration_minutes": 0,
                "warning": "Using Haversine approximation (OSRM unavailable)"
            })
        
        if not osrm_data.get("routes"):
            logger.warning("❌ No routes found from OSRM")
            haversine_dist = calculate_haversine(origin_lat, origin_lon, dest_lat, dest_lon)
            return Response({
                "distance_meters": int(haversine_dist),
                "distance_km": round(haversine_dist / 1000, 2),
                "duration_seconds": 0,
                "duration_minutes": 0,
                "warning": "Using Haversine approximation (no routes found)"
            })
        
        route = osrm_data["routes"][0]
        distance_meters = int(route.get("distance", 0))
        duration_seconds = int(route.get("duration", 0))
        
        logger.info(f"✅ OSRM distance calculated: {distance_meters}m ({distance_meters/1000:.2f}km), {duration_seconds}s")
        
        return Response({
            "distance_meters": distance_meters,
            "distance_km": round(distance_meters / 1000, 2),
            "duration_seconds": duration_seconds,
            "duration_minutes": round(duration_seconds / 60, 2)
        })
    
    except requests.RequestException as e:
        logger.error(f"❌ OSRM request failed: {e}")
        # Fallback to Haversine
        try:
            origin = request.data.get('origin', {})
            destination = request.data.get('destination', {})
            haversine_dist = calculate_haversine(
                origin.get('lat'), origin.get('lon'),
                destination.get('lat'), destination.get('lon')
            )
            return Response({
                "distance_meters": int(haversine_dist),
                "distance_km": round(haversine_dist / 1000, 2),
                "duration_seconds": 0,
                "duration_minutes": 0,
                "warning": f"Using Haversine approximation (OSRM failed: {str(e)})"
            })
        except:
            return Response(
                {'error': f'Distance calculation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def calculate_haversine(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two points using Haversine formula.
    Returns distance in meters.
    """
    from math import sin, cos, sqrt, atan2, radians
    
    R = 6371000  # Earth radius in meters
    
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c
