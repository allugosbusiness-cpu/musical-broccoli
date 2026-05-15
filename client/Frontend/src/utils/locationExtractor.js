/**
 * Location Extractor Utility
 * Robust coordinate extraction from various truck data formats
 * Handles: current_location objects, lat/lon strings, legacy coordinates, etc.
 */

/**
 * Extract latitude from truck data in any format
 * Priority: current_location.lat > current_location.latitude > truck.latitude > truck.last_latitude
 */
export function extractLatitude(truck) {
  if (!truck) return null;

  // Priority 1: current_location object with lat/latitude
  if (truck.current_location && typeof truck.current_location === 'object') {
    if (truck.current_location.lat !== undefined && truck.current_location.lat !== null) {
      const lat = parseFloat(truck.current_location.lat);
      if (Number.isFinite(lat)) return lat;
    }
    if (truck.current_location.latitude !== undefined && truck.current_location.latitude !== null) {
      const lat = parseFloat(truck.current_location.latitude);
      if (Number.isFinite(lat)) return lat;
    }
  }

  // Priority 2: current_location as string "lat,lon"
  if (truck.current_location && typeof truck.current_location === 'string') {
    const parts = truck.current_location.split(',').map(p => parseFloat(p.trim()));
    if (parts.length >= 1 && Number.isFinite(parts[0])) {
      return parts[0];
    }
  }

  // Priority 3: location object (alternative format)
  if (truck.location && typeof truck.location === 'object') {
    if (truck.location.lat !== undefined && truck.location.lat !== null) {
      const lat = parseFloat(truck.location.lat);
      if (Number.isFinite(lat)) return lat;
    }
    if (truck.location.latitude !== undefined && truck.location.latitude !== null) {
      const lat = parseFloat(truck.location.latitude);
      if (Number.isFinite(lat)) return lat;
    }
  }

  // Priority 4: Direct latitude field
  if (truck.latitude !== undefined && truck.latitude !== null) {
    const lat = parseFloat(truck.latitude);
    if (Number.isFinite(lat)) return lat;
  }

  // Priority 5: last_latitude (legacy field)
  if (truck.last_latitude !== undefined && truck.last_latitude !== null) {
    const lat = parseFloat(truck.last_latitude);
    if (Number.isFinite(lat)) return lat;
  }

  return null;
}

/**
 * Extract longitude from truck data in any format
 * Priority: current_location.lon > current_location.longitude > truck.longitude > truck.last_longitude
 */
export function extractLongitude(truck) {
  if (!truck) return null;

  // Priority 1: current_location object with lon/longitude
  if (truck.current_location && typeof truck.current_location === 'object') {
    if (truck.current_location.lon !== undefined && truck.current_location.lon !== null) {
      const lon = parseFloat(truck.current_location.lon);
      if (Number.isFinite(lon)) return lon;
    }
    if (truck.current_location.longitude !== undefined && truck.current_location.longitude !== null) {
      const lon = parseFloat(truck.current_location.longitude);
      if (Number.isFinite(lon)) return lon;
    }
  }

  // Priority 2: current_location as string "lat,lon"
  if (truck.current_location && typeof truck.current_location === 'string') {
    const parts = truck.current_location.split(',').map(p => parseFloat(p.trim()));
    if (parts.length >= 2 && Number.isFinite(parts[1])) {
      return parts[1];
    }
  }

  // Priority 3: location object (alternative format)
  if (truck.location && typeof truck.location === 'object') {
    if (truck.location.lon !== undefined && truck.location.lon !== null) {
      const lon = parseFloat(truck.location.lon);
      if (Number.isFinite(lon)) return lon;
    }
    if (truck.location.longitude !== undefined && truck.location.longitude !== null) {
      const lon = parseFloat(truck.location.longitude);
      if (Number.isFinite(lon)) return lon;
    }
  }

  // Priority 4: Direct longitude field
  if (truck.longitude !== undefined && truck.longitude !== null) {
    const lon = parseFloat(truck.longitude);
    if (Number.isFinite(lon)) return lon;
  }

  // Priority 5: last_longitude (legacy field)
  if (truck.last_longitude !== undefined && truck.last_longitude !== null) {
    const lon = parseFloat(truck.last_longitude);
    if (Number.isFinite(lon)) return lon;
  }

  return null;
}

/**
 * Extract both coordinates at once
 * Returns: { lat, lon, source }
 * source indicates where the data came from (e.g., "current_location", "direct", "legacy")
 */
export function extractCoordinates(truck) {
  const lat = extractLatitude(truck);
  const lon = extractLongitude(truck);

  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return { lat: null, lon: null, source: 'missing' };
  }

  // Determine source
  let source = 'unknown';
  if (truck.current_location && typeof truck.current_location === 'object') {
    source = 'current_location_object';
  } else if (truck.current_location && typeof truck.current_location === 'string') {
    source = 'current_location_string';
  } else if (truck.latitude !== undefined && truck.longitude !== undefined) {
    source = 'direct_coords';
  } else if (truck.last_latitude !== undefined && truck.last_longitude !== undefined) {
    source = 'legacy_coords';
  }

  return { lat, lon, source };
}

/**
 * Check if coordinates are valid
 */
export function isValidCoordinate(lat, lon) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return false;
  if (lat < -90 || lat > 90) return false;
  if (lon < -180 || lon > 180) return false;
  return true;
}

/**
 * Get truck location status
 * Returns: 'valid', 'pending', 'invalid'
 */
export function getLocationStatus(truck) {
  const { lat, lon } = extractCoordinates(truck);
  
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return 'pending';  // No location yet
  }
  
  if (isValidCoordinate(lat, lon)) {
    return 'valid';
  }
  
  return 'invalid';  // Coordinates outside valid range
}

/**
 * Format coordinates for display
 */
export function formatCoordinates(lat, lon, precision = 4) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return 'No location';
  }
  return `${lat.toFixed(precision)}, ${lon.toFixed(precision)}`;
}
