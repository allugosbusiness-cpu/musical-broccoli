"""
Location endpoints for autocomplete and reverse geocoding
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from math import radians, cos, sin, asin, sqrt

from .location_suggestions import search_locations, get_locations_by_type, ZIMBABWE_LOCATIONS, MANICALAND_LOCATIONS


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
    Autocomplete location search.
    Query params: q (search query)
    Returns: { results: [{name, lat, lon, type}] }
    """
    try:
        query = request.query_params.get('q', '')
        results = search_locations(query, limit=10)
        
        return Response({
            'results': results
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )