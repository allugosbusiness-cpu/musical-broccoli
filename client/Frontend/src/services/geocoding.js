/**
 * Reverse Geocoding Service
 * Converts coordinates (lat, lon) to human-readable addresses
 * Priority: Backend API > Nominatim/OpenStreetMap
 */

// Cache to avoid repeated API calls for the same coordinates
const geocodeCache = new Map();

const NOMINATIM_API = 'https://nominatim.openstreetmap.org/reverse';

const getApiV1Base = () => {
  if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api/v1';
  return 'https://pulsetrack-back.onrender.com/api/v1';
};

export const reverseGeocode = async (lat, lon) => {
  // Validate coordinates
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return 'Invalid location';
  }
  
  // Create cache key with safe formatting
  const cacheKey = `${Number(lat).toFixed(4)},${Number(lon).toFixed(4)}`;
  
  // Check cache first
  if (geocodeCache.has(cacheKey)) {
    return geocodeCache.get(cacheKey);
  }

  try {
    // ✅ NEW: Try backend API first (faster, supports custom locations)
    try {
      const apiResponse = await fetch(
        `${getApiV1Base()}/locations/reverse-geocode/?lat=${lat}&lon=${lon}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );

      if (apiResponse.ok) {
        const apiData = await apiResponse.json();
        if (apiData.name) {
          const result = apiData.name;
          geocodeCache.set(cacheKey, result);
          console.log(`✅ Reverse geocoding (backend): ${Number(lat).toFixed(4)}, ${Number(lon).toFixed(4)} → ${result}`);
          return result;
        }
      }
    } catch (apiError) {
      console.warn('⚠️ Backend reverse geocoding failed, trying Nominatim:', apiError.message);
    }

    // Fallback to Nominatim API
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
    const result = displayAddress || `${Number(lat).toFixed(3)}, ${Number(lon).toFixed(3)}`;
    
    // Cache the result
    geocodeCache.set(cacheKey, result);
    console.log(`✅ Reverse geocoding (Nominatim): ${Number(lat).toFixed(4)}, ${Number(lon).toFixed(4)} → ${result}`);
    return result;
  } catch (error) {
    console.error('❌ Reverse geocoding error:', error);
    // Return coordinates as fallback
    const fallback = `${Number(lat).toFixed(3)}, ${Number(lon).toFixed(3)}`;
    geocodeCache.set(cacheKey, fallback);
    return fallback;
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
