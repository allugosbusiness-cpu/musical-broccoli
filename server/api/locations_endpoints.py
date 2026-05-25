"""
Location endpoints for autocomplete and reverse geocoding
Uses OSM Nominatim proxy with client-side caching for privacy and rate limiting
No hardcoded location data — all results come from OSM Nominatim (free geocoding service)
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .geocoding_proxy import search_nominatim, reverse_geocode_nominatim
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def reverse_geocode(request):
    """
    Reverse geocode: Find the nearest named location for given lat/lon.
    Uses OSM Nominatim via the proxy (cached, rate-limited).
    
    Query params: lat, lon
    Returns: { name, lat, lon, type, display_name }
    """
    try:
        lat = float(request.query_params.get('lat', 0))
        lon = float(request.query_params.get('lon', 0))

        if not lat or not lon:
            return Response(
                {'error': 'lat and lon query parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use OSM Nominatim for reverse geocoding
        result = reverse_geocode_nominatim(lat, lon)

        if result:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response({
                'name': f'Approx: {round(lat, 4)}, {round(lon, 4)}',
                'lat': lat,
                'lon': lon,
                'type': 'unknown',
                'source': 'approximate',
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
    Autocomplete location search using OSM Nominatim (free, no API key needed).
    Query params: q (search query)
    Returns: { results: [{name, lat, lon, type, source}] }
    
    All results come from OSM Nominatim — no hardcoded location lists.
    Server-side caching + rate limiting protects Nominatim's free tier.
    Client-side caching (localStorage) further reduces API calls.
    """
    try:
        query = request.query_params.get('q', '').strip()
        source = request.query_params.get('source', 'auto')

        if not query or len(query) < 2:
            return Response({'results': []}, status=status.HTTP_200_OK)

        results = []

        # Try Nominatim (cached + rate-limited server-side)
        if source in ('auto', 'nominatim'):
            try:
                nominatim_results = search_nominatim(query, limit=10)
                if nominatim_results:
                    results = nominatim_results
            except Exception as e:
                logger.warning(f"Nominatim search failed: {e}")

        # Limit total results
        results = results[:15]

        return Response({
            'results': results,
            'count': len(results),
            'source': source,
            'query': query,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f'Location autocomplete error: {str(e)}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )