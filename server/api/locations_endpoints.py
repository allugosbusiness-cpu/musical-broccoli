"""
Location suggestions API endpoints
Provides location search and autocomplete for mission creation
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .location_suggestions import search_locations, get_locations_by_type, get_all_location_types

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def location_search(request):
    """
    GET /api/v1/locations/search/?q=mutare&limit=10
    
    Search for locations by name
    
    Query parameters:
    - q: Search query (location name)
    - limit: Maximum number of results (default: 10)
    - type: Filter by location type (optional)
    """
    try:
        query = request.GET.get('q', '')
        limit = int(request.GET.get('limit', 10))
        location_type = request.GET.get('type', None)
        
        if location_type:
            locations = get_locations_by_type(location_type, limit)
        else:
            locations = search_locations(query, limit)
        
        logger.info(f"📍 Location search: '{query}' type={location_type} found {len(locations)} results")
        
        return JsonResponse({
            'query': query,
            'count': len(locations),
            'results': locations,
        }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Location search error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def location_types(request):
    """
    GET /api/v1/locations/types/
    
    Get all available location types for filtering
    """
    try:
        types = get_all_location_types()
        logger.info(f"📍 Location types requested: {len(types)} types available")
        
        return JsonResponse({
            'count': len(types),
            'types': types,
        }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Location types error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def location_autocomplete(request):
    """
    GET /api/v1/locations/autocomplete/?q=sch
    
    Autocomplete locations for dropdowns
    Limited results (5) for performance
    """
    try:
        query = request.GET.get('q', '')
        
        if len(query) < 2:
            return JsonResponse({
                'query': query,
                'results': [],
            }, status=200)
        
        locations = search_locations(query, 5)
        
        return JsonResponse({
            'query': query,
            'count': len(locations),
            'results': [
                {
                    'id': f"{loc['lat']},{loc['lon']}",
                    'name': loc['name'],
                    'type': loc['type'],
                    'lat': loc['lat'],
                    'lon': loc['lon'],
                }
                for loc in locations
            ],
        }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Autocomplete error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def location_reverse_geocode(request):
    """
    GET /api/v1/locations/reverse-geocode/?lat=-17.8&lon=31.0
    
    Reverse geocode coordinates to find nearby location names
    Returns closest known location or generates a location name from coordinates
    """
    try:
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        
        if lat is None or lon is None:
            return JsonResponse({
                'error': 'lat and lon parameters required'
            }, status=400)
        
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return JsonResponse({
                'error': 'Invalid latitude or longitude'
            }, status=400)
        
        # ✅ NEW: Accept and suggest any location
        # Find closest location from database
        from .models_v2 import FleetLocation
        try:
            locations = FleetLocation.objects.all()
            if not locations.exists():
                # If no database locations, create generic suggestion
                return JsonResponse({
                    'lat': lat,
                    'lon': lon,
                    'name': f'Location ({lat:.4f}, {lon:.4f})',
                    'accuracy': 'custom',
                    'type': 'custom_coordinates'
                }, status=200)
            
            # Find closest location using simple distance calculation
            closest = None
            min_distance = float('inf')
            for loc in locations:
                # Simple Haversine distance
                from math import radians, cos, sin, asin, sqrt
                lon1, lat1, lon2, lat2 = map(radians, [loc.longitude, loc.latitude, lon, lat])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                km = 6371 * c
                
                if km < min_distance:
                    min_distance = km
                    closest = loc
            
            if closest and min_distance < 5:  # Within 5km
                return JsonResponse({
                    'lat': lat,
                    'lon': lon,
                    'name': closest.name,
                    'closest_location': closest.name,
                    'distance_km': round(min_distance, 2),
                    'type': closest.location_type,
                    'accuracy': 'nearby'
                }, status=200)
            else:
                # Return custom location with coordinates
                return JsonResponse({
                    'lat': lat,
                    'lon': lon,
                    'name': f'Location ({lat:.4f}, {lon:.4f})',
                    'accuracy': 'custom',
                    'type': 'custom_coordinates',
                    'nearest_km': round(min_distance, 2) if closest else None
                }, status=200)
        except Exception as db_err:
            logger.warning(f"⚠️ Database lookup failed: {str(db_err)}, returning generic location")
            return JsonResponse({
                'lat': lat,
                'lon': lon,
                'name': f'Location ({lat:.4f}, {lon:.4f})',
                'accuracy': 'custom',
                'type': 'custom_coordinates'
            }, status=200)
        
    except Exception as e:
        logger.error(f"❌ Reverse geocoding error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
