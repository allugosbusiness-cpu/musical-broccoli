/**
 * Road-Matched Trail Service
 * Handles OSRM routing, caching, off-route detection, and trail management
 */

const OSRM_BASE_URL = 'https://router.project-osrm.org/route/v1/driving';
const REROUTE_DEBOUNCE_MS = 5000;  // 5-10s debounce window
const OFF_ROUTE_THRESHOLD_METERS = 50;  // Configurable threshold
const CACHE_MAX_AGE_MS = 300000;  // 5 minutes

// Response cache: key = waypoint triple hash, value = { response, timestamp }
const responseCache = new Map();

// Reroute debounce timers per truck
const rerouteTimers = new Map();

// Trail state per truck
const trailState = new Map();

/**
 * Hash waypoint triple to create cache key
 */
function hashWaypoints(origin, current, destination) {
  const key = `${origin.lat},${origin.lng}|${current.lat},${current.lng}|${destination.lat},${destination.lng}`;
  let hash = 0;
  for (let i = 0; i < key.length; i++) {
    const char = key.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(16);
}

/**
 * Calculate distance between two points (Haversine formula)
 */
export function calculateDistance(lat1, lng1, lat2, lng2) {
  const R = 6371000; // Earth radius in meters
  const rad1 = (lat1 * Math.PI) / 180;
  const rad2 = (lat2 * Math.PI) / 180;
  const deltaLat = ((lat2 - lat1) * Math.PI) / 180;
  const deltaLng = ((lng2 - lng1) * Math.PI) / 180;

  const a =
    Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
    Math.cos(rad1) * Math.cos(rad2) * Math.sin(deltaLng / 2) * Math.sin(deltaLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

/**
 * Decode polyline6 format (OSRM default)
 */
function decodePolyline6(encoded) {
  const points = [];
  let index = 0;
  let lat = 0;
  let lng = 0;
  let change = 0;

  while (index < encoded.length) {
    let result = 0;
    let shift = 0;
    do {
      change = encoded.charCodeAt(index++) - 63;
      result |= (change & 0x1f) << shift;
      shift += 5;
    } while (change >= 0x20);
    const dLat = (result & 1) ? ~(result >> 1) : result >> 1;
    lat += dLat;

    result = 0;
    shift = 0;
    do {
      change = encoded.charCodeAt(index++) - 63;
      result |= (change & 0x1f) << shift;
      shift += 5;
    } while (change >= 0x20);
    const dLng = (result & 1) ? ~(result >> 1) : result >> 1;
    lng += dLng;

    points.push({
      lat: lat / 1e6,
      lng: lng / 1e6,
    });
  }
  return points;
}

/**
 * Check if cached response is still valid
 */
function isCacheValid(timestamp) {
  return Date.now() - timestamp < CACHE_MAX_AGE_MS;
}

/**
 * Main function: Get route via OSRM or cache
 * @param {Object} origin - {lat, lng}
 * @param {Object} current - {lat, lng}
 * @param {Object} destination - {lat, lng}
 * @param {Object} options - {useCache, timeout}
 * @returns {Promise<{geometry, steps, distance, duration, via}>}
 */
export async function getRoute(origin, current, destination, options = {}) {
  const { useCache = true, timeout = 10000 } = options;

  // Create cache key
  const cacheKey = hashWaypoints(origin, current, destination);

  // Check cache first
  if (useCache && responseCache.has(cacheKey)) {
    const cached = responseCache.get(cacheKey);
    if (isCacheValid(cached.timestamp)) {
      console.log('📦 Using cached OSRM response for route');
      return cached.response;
    }
  }

  try {
    // Build OSRM request with three waypoints
    const coords = `${origin.lng},${origin.lat};${current.lng},${current.lat};${destination.lng},${destination.lat}`;
    const url = `${OSRM_BASE_URL}/${coords}?overview=full&geometries=polyline6&steps=true&annotations=speed,duration`;

    console.log('🗺️ Requesting OSRM route:', { origin, current, destination });

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`OSRM error: ${response.status}`);
    }

    const data = await response.json();

    if (!data.routes || data.routes.length === 0) {
      throw new Error('No route found');
    }

    const route = data.routes[0];

    // Decode polyline6 geometry
    const geometry = decodePolyline6(route.geometry);

    const result = {
      geometry,
      steps: route.legs,
      distance: route.distance,
      duration: route.duration,
      via: current, // Middle waypoint (current location)
      requestedAt: new Date().toISOString(),
    };

    // Cache the response
    if (useCache) {
      responseCache.set(cacheKey, {
        response: result,
        timestamp: Date.now(),
      });
      console.log('✅ Cached OSRM response');
    }

    return result;
  } catch (error) {
    console.error('❌ OSRM request failed:', error.message);
    // Return null so caller can handle fallback (e.g., local snapping)
    return null;
  }
}

/**
 * Find nearest point on route to GPS position
 */
function findNearestPointOnRoute(route, gpsLat, gpsLng) {
  let nearestDist = Infinity;
  let nearestIndex = 0;
  let nearestPoint = route[0];

  route.forEach((point, idx) => {
    const dist = calculateDistance(gpsLat, gpsLng, point.lat, point.lng);
    if (dist < nearestDist) {
      nearestDist = dist;
      nearestIndex = idx;
      nearestPoint = point;
    }
  });

  return {
    point: nearestPoint,
    index: nearestIndex,
    distance: nearestDist,
  };
}

/**
 * Detect if truck has deviated off route
 * @param {Array} routeGeometry - Polyline points from OSRM
 * @param {number} gpsLat
 * @param {number} gpsLng
 * @param {number} thresholdMeters - Default OFF_ROUTE_THRESHOLD_METERS
 * @returns {Object} {isOffRoute, distanceOffRoute, nearestPoint}
 */
export function detectOffRoute(routeGeometry, gpsLat, gpsLng, thresholdMeters = OFF_ROUTE_THRESHOLD_METERS) {
  if (!routeGeometry || routeGeometry.length < 2) {
    return { isOffRoute: false, distanceOffRoute: 0, nearestPoint: null };
  }

  const { point, distance } = findNearestPointOnRoute(routeGeometry, gpsLat, gpsLng);

  const isOffRoute = distance > thresholdMeters;

  if (isOffRoute) {
    console.warn(`⚠️ Truck off-route! Distance: ${distance.toFixed(0)}m > ${thresholdMeters}m threshold`);
  }

  return {
    isOffRoute,
    distanceOffRoute: distance,
    nearestPoint: point,
  };
}

/**
 * Schedule a debounced reroute request
 */
export function scheduleReroute(
  truckId,
  origin,
  current,
  destination,
  onReroute,
  debounceMs = REROUTE_DEBOUNCE_MS
) {
  // Clear existing timer
  if (rerouteTimers.has(truckId)) {
    clearTimeout(rerouteTimers.get(truckId));
  }

  // Schedule new reroute
  const timerId = setTimeout(async () => {
    console.log(`🔄 Rerouting truck ${truckId}...`);
    const newRoute = await getRoute(origin, current, destination);

    if (newRoute) {
      onReroute(truckId, newRoute);
      console.log(`✅ Reroute complete for ${truckId}`);
    } else {
      console.warn(`⚠️ Reroute failed for ${truckId}, keeping current route`);
    }

    rerouteTimers.delete(truckId);
  }, debounceMs);

  rerouteTimers.set(truckId, timerId);
}

/**
 * Splice new polyline into existing trail (smooth transition)
 */
export function spliceTrail(
  existingGeometry,
  newGeometry,
  spliceIndex = 0,
  preserveHistoricalMs = 10000
) {
  // Keep historical data for visualization
  const timestamp = Date.now();

  // Find the best splice point in new geometry near the GPS current position
  const splicedGeometry = [
    ...existingGeometry.slice(0, spliceIndex),
    ...newGeometry,
  ];

  return {
    geometry: splicedGeometry,
    splicePoint: spliceIndex,
    timestamp,
    preserveUntil: timestamp + preserveHistoricalMs,
  };
}

/**
 * Store trail state for a truck
 */
export function updateTrailState(truckId, trailData) {
  trailState.set(truckId, {
    ...trailState.get(truckId),
    ...trailData,
    lastUpdated: Date.now(),
  });
}

/**
 * Get trail state for a truck
 */
export function getTrailState(truckId) {
  return trailState.get(truckId) || null;
}

/**
 * Clear expired trail data
 */
export function clearExpiredTrails() {
  const now = Date.now();
  for (const [truckId, state] of trailState.entries()) {
    if (state.preserveUntil && now > state.preserveUntil) {
      trailState.delete(truckId);
    }
  }
}

/**
 * Clear all caches (useful for testing or manual reset)
 */
export function clearCaches() {
  responseCache.clear();
  trailState.clear();
  for (const timerId of rerouteTimers.values()) {
    clearTimeout(timerId);
  }
  rerouteTimers.clear();
}

/**
 * Get cache stats for monitoring
 */
export function getCacheStats() {
  return {
    cachedRoutes: responseCache.size,
    trackedTrucks: trailState.size,
    pendingReroutes: rerouteTimers.size,
  };
}

export default {
  getRoute,
  detectOffRoute,
  scheduleReroute,
  spliceTrail,
  updateTrailState,
  getTrailState,
  clearExpiredTrails,
  clearCaches,
  getCacheStats,
  calculateDistance,
  decodePolyline6,
  OFF_ROUTE_THRESHOLD_METERS,
  REROUTE_DEBOUNCE_MS,
};
