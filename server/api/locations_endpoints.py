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
