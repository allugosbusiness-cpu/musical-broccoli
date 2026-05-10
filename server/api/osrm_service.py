"""
Route generation service using OSRM.
Handles route matching and geometry computation.
"""

import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"
OSRM_MATCH = "https://router.project-osrm.org/match/v1/driving"
TIMEOUT_SECONDS = 10


def compute_route_geometry(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    waypoints: Optional[list] = None
) -> Optional[Dict[str, Any]]:
    """
    Compute a route from origin to destination using OSRM.
    Returns GeoJSON LineString geometry.
    
    Args:
        origin_lat, origin_lng: Starting point
        dest_lat, dest_lng: Destination point
        waypoints: Optional list of intermediate points [{lat, lng}, ...]
    
    Returns:
        Dict with 'geometry' (GeoJSON LineString), 'distance', 'duration', or None if failed
    """
    try:
        # Build coordinate string: lon,lat;lon,lat;...
        coords = f"{origin_lng},{origin_lat}"
        
        if waypoints:
            for wp in waypoints:
                coords += f";{wp.get('lng', wp.get('lon'))},{wp.get('lat')}"
        
        coords += f";{dest_lng},{dest_lat}"
        
        # Build OSRM request
        url = f"{OSRM_BASE}/{coords}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
            "annotations": "distance,duration"
        }
        
        logger.info(f"🛣️ Computing route: {url}")
        
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("code") != "Ok":
            logger.error(f"❌ OSRM error: {data.get('code')} - {data.get('message', '')}")
            return None
        
        if not data.get("routes"):
            logger.warning("❌ No routes found")
            return None
        
        route = data["routes"][0]
        
        result = {
            "geometry": route.get("geometry"),
            "distance": route.get("distance"),
            "duration": route.get("duration"),
            "legs": route.get("legs"),
        }
        
        logger.info(f"✅ Route computed: {result['distance']/1000:.2f}km, {result['duration']/60:.0f}min")
        
        return result
    
    except requests.Timeout:
        logger.error("⏱️ OSRM request timeout")
        return None
    except requests.RequestException as e:
        logger.error(f"❌ OSRM request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error in route computation: {e}")
        return None


def match_gps_trace(
    gps_points: list
) -> Optional[Dict[str, Any]]:
    """
    Match raw GPS points to the road network using OSRM map-matching.
    
    Args:
        gps_points: List of {lat, lng, ...} points in order
    
    Returns:
        Dict with 'geometry' and matched data, or None if failed
    """
    try:
        if len(gps_points) < 2:
            logger.warning("❌ Need at least 2 GPS points for matching")
            return None
        
        # Build coordinate string
        coords = ";".join([
            f"{p.get('lng', p.get('lon'))},{p.get('lat')}"
            for p in gps_points
        ])
        
        url = f"{OSRM_MATCH}/{coords}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
            "annotations": "distance,duration"
        }
        
        logger.info(f"🔄 Matching {len(gps_points)} GPS points...")
        
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("code") != "Ok":
            logger.error(f"❌ OSRM match error: {data.get('code')}")
            return None
        
        if not data.get("matchings"):
            logger.warning("❌ No matches found")
            return None
        
        matching = data["matchings"][0]
        
        result = {
            "geometry": matching.get("geometry"),
            "distance": matching.get("distance"),
            "duration": matching.get("duration"),
            "confidence": matching.get("confidence"),
        }
        
        logger.info(f"✅ GPS matched: {result['distance']/1000:.2f}km (confidence: {result['confidence']:.2%})")
        
        return result
    
    except Exception as e:
        logger.error(f"❌ GPS matching failed: {e}")
        return None
