/**
 * Reverse Geocoding Service
 * Converts coordinates (lat, lon) to human-readable addresses
 */

// Cache to avoid repeated API calls for the same coordinates
const geocodeCache = new Map();

const NOMINATIM_API = 'https://nominatim.openstreetmap.org/reverse';

export const reverseGeocode = async (lat, lon) => {
  // Create cache key
  const cacheKey = `${lat.toFixed(4)},${lon.toFixed(4)}`;
  
  // Check cache first
  if (geocodeCache.has(cacheKey)) {
    return geocodeCache.get(cacheKey);
  }

  try {
    const response = await fetch(
      `${NOMINATIM_API}?format=json&lat=${lat}&lon=${lon}&zoom=16&addressdetails=1`,
      {
        headers: {
          'User-Agent': 'PulseTrack App',
        }
      }
    );

    if (!response.ok) {
      throw new Error(`Geocoding failed: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Extract a human-readable address
    const address = data.address || {};
    let displayAddress = '';
    
    // Try to build a meaningful address
    if (address.road || address.village || address.town || address.city) {
      const road = address.road ? `${address.road}` : '';
      const city = address.city || address.town || address.village || '';
      displayAddress = `${road}${road && city ? ', ' : ''}${city}`;
    } else if (address.county) {
      displayAddress = address.county;
    } else if (data.name) {
      displayAddress = data.name;
    }

    // Fallback to coordinates if no address found
    const result = displayAddress || `${lat.toFixed(3)}, ${lon.toFixed(3)}`;
    
    // Cache the result
    geocodeCache.set(cacheKey, result);
    return result;
  } catch (error) {
    console.error('❌ Reverse geocoding error:', error);
    // Return coordinates as fallback
    return `${lat.toFixed(3)}, ${lon.toFixed(3)}`;
  }
};

export const batchReverseGeocode = async (locations) => {
  /**
   * Geocode multiple locations in parallel
   * locations: Array of {lat, lon} objects
   * Returns: Promise<Array of addresses>
   */
  return Promise.all(
    locations.map(loc => reverseGeocode(loc.lat, loc.lon))
  );
};

export const clearGeocodeCache = () => {
  geocodeCache.clear();
};
