"""
Location endpoints for autocomplete and reverse geocoding
Uses OSM Nominatim proxy with local fallback for offline/resilience
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from math import radians, cos, sin, asin, sqrt

from .location_suggestions import search_locations, get_locations_by_type, ZIMBABWE_LOCATIONS, MANICALAND_LOCATIONS
from .geocoding_proxy import search_nominatim, reverse_geocode_nominatim
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def reverse_geocode(request):
    """
    Reverse geocode: Find the nearest named location for given lat/lon.
    Searches through the local Zimbabwe location database and returns
    the closest matching location name.
    
    Query params: lat, lon
    Returns: { name, lat, lon, type, distance_km }
    """
    try:
        lat = float(request.query_params.get('lat', 0))
        lon = float(request.query_params.get('lon', 0))
        
        if not lat or not lon:
            return Response(
                {'error': 'lat and lon query parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        all_locations = MANICALAND_LOCATIONS + ZIMBABWE_LOCATIONS
        
        # Find nearest location using Haversine distance
        nearest = None
        nearest_distance = float('inf')
        
        for loc in all_locations:
            # Haversine
            dlat = radians(loc['lat'] - lat)
            dlon = radians(loc['lon'] - lon)
            a = sin(dlat/2)**2 + cos(radians(lat)) * cos(radians(loc['lat'])) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            distance = 6371 * c  # km
            
            if distance < nearest_distance:
                nearest_distance = distance
                nearest = loc
        
        if nearest and nearest_distance < 100:  # Only return if within 100km
            return Response({
                'name': nearest['name'],
                'lat': nearest['lat'],
                'lon': nearest['lon'],
                'type': nearest['type'],
                'distance_km': round(nearest_distance, 2)
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'name': f'Approx: {round(lat, 4)}, {round(lon, 4)}',
                'lat': lat,
                'lon': lon,
                'type': 'unknown',
                'distance_km': 0
            }, status=status.HTTP_200_OK)
            
    except (TypeError, ValueError) as e:
        return Response(
            {'error': f'Invalid coordinates: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def location_autocomplete(request):
    """
    Autocomplete location search using OSM Nominatim with local fallback.
    Query params: q (search query)
    Returns: { results: [{name, lat, lon, type}] }
    
    Strategy:
    1. Try Nominatim first (cached, rate-limited)
    2. Fall back to local Zimbabwe location database
    3. Return empty results if both fail
    """
    try:
        query = request.query_params.get('q', '').strip()
        source = request.query_params.get('source', 'auto')
        
        if not query or len(query) < 2:
            return Response({'results': []}, status=status.HTTP_200_OK)
        
        results = []
        
        # 1. Try Nominatim for any query (cached server-side)
        if source in ('auto', 'nominatim'):
            try:
                nominatim_results = search_nominatim(query, limit=10)
                if nominatim_results:
                    results.extend(nominatim_results)
            except Exception as e:
                logger.warning(f"Nominatim search failed, using local fallback: {e}")
        
        # 2. Always add local Zimbabwe results as supplement
        try:
            local_results = search_locations(query, limit=5)
            for local in local_results:
                # Add local results with explicit local marker
                local['source'] = 'local'
                results.append(local)
        except Exception as e:
            logger.warning(f"Local search failed: {e}")
        
        # Deduplicate by name (Nominatim might return similar to local)
        seen_names = set()
        deduped = []
        for r in results:
            name_key = r.get('name', '').lower()[:30]
            if name_key not in seen_names:
                seen_names.add(name_key)
                deduped.append(r)
        
        # Limit total results
        deduped = deduped[:15]
        
        return Response({
            'results': deduped,
            'count': len(deduped),
            'source': source,
            'query': query,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Location autocomplete error: {str(e)}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
