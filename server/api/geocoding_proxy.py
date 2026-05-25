"""
OSM Nomninatim Geocoding Proxy with Caching
Provides OSM-backed autocomplete/geocoding without hardcoded lists
Respects Nominatim usage policy:
- Max 1 request per second
- Uses descriptive User-Agent
- Caches results to reduce load
"""

import requests
import json
import time
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Nominatim endpoint (free tier, requires HTTPS)
NOMINATIM_BASE = "https://nominatim.openstreetmap.org"

# Cache TTL: 24 hours for search results (locations don't change often)
CACHE_TTL_SECONDS = 86400

# Rate limiting: last request time
_last_request_time = 0
MIN_INTERVAL_SECONDS = 1.1  # Nominatim requires max 1 req/sec

# Custom User-Agent per Nominatim policy
USER_AGENT = "PulseTrackFleet/1.0 (Mutare ZW fleet management; contact@pulsetrack.com)"


def _rate_limit():
    """Ensure we don't exceed Nominatim's 1 request per second limit"""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_INTERVAL_SECONDS:
        sleep_time = MIN_INTERVAL_SECONDS - elapsed
        time.sleep(sleep_time)
    _last_request_time = time.time()


def search_nominatim(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for locations using Nominatim API.
    Returns list of {name, lat, lon, type, display_name}
    """
    cache_key = f"nominatim_search_{query.lower()}_{limit}"
    
    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"✅ Nominatim cache hit for: {query}")
        return cached
    
    try:
        _rate_limit()
        
        params = {
            'q': query,
            'format': 'json',
            'addressdetails': 1,
            'limit': limit,
            'accept-language': 'en',
        }
        
        headers = {
            'User-Agent': USER_AGENT,
        }
        
        response = requests.get(
            f"{NOMINATIM_BASE}/search",
            params=params,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        results = []
        for place in response.json():
            lat = place.get('lat')
            lon = place.get('lon')
            if lat and lon:
                results.append({
                    'name': place.get('display_name', place.get('name', query)).split(',')[0],
                    'full_name': place.get('display_name', query),
                    'lat': float(lat),
                    'lon': float(lon),
                    'type': place.get('type', 'unknown'),
                    'category': place.get('category', ''),
                    'source': 'nominatim',
                })
        
        # Cache the results
        cache.set(cache_key, results, CACHE_TTL_SECONDS)
        logger.info(f"✅ Nominatim search for '{query}': {len(results)} results (cached)")
        
        return results
        
    except requests.exceptions.Timeout:
        logger.warning(f"⏱️ Nominatim timeout for query: {query}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Nominatim request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Nominatim search error: {e}")
        return []


def reverse_geocode_nominatim(lat: float, lon: float) -> Optional[Dict]:
    """
    Reverse geocode using Nominatim.
    Returns {name, lat, lon, type, display_name, address}
    """
    cache_key = f"nominatim_reverse_{lat:.4f}_{lon:.4f}"
    
    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"✅ Nominatim reverse cache hit for: {lat}, {lon}")
        return cached
    
    try:
        _rate_limit()
        
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
        }
        
        headers = {
            'User-Agent': USER_AGENT,
        }
        
        response = requests.get(
            f"{NOMINATIM_BASE}/reverse",
            params=params,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data and 'display_name' in data:
            result = {
                'name': data.get('name', data.get('display_name', 'Unknown').split(',')[0]),
                'full_name': data.get('display_name', 'Unknown'),
                'lat': lat,
                'lon': lon,
                'type': data.get('type', 'unknown'),
                'address': data.get('address', {}),
                'source': 'nominatim',
            }
            
            # Cache for 7 days (addresses change infrequently)
            cache.set(cache_key, result, CACHE_TTL_SECONDS)
            logger.info(f"✅ Nominatim reverse geocode: {result['name']}")
            
            return result
        
        return None
        
    except requests.exceptions.Timeout:
        logger.warning(f"⏱️ Nominatim reverse timeout for: {lat}, {lon}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Nominatim reverse request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Nominatim reverse error: {e}")
        return None