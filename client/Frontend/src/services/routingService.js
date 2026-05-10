/**
 * Routing Service - OSRM-based routing engine
 * Provides road-following routes between coordinates
 * Uses OpenStreetMap Routing Machine (OSRM) for free routing
 */

const OSRM_BASE = 'https://router.project-osrm.org/route/v1/driving';
const TIMEOUT_MS = 8000;
const RETRY_ATTEMPTS = 2;
const RETRY_DELAY_MS = 1000;

/**
 * Create a fallback route (straight line) when OSRM fails
 * This ensures we always have SOME visualization instead of nothing
 * @param {Object} origin - {lat, lng}
 * @param {Object} destination - {lat, lng}
 * @returns {Object} Basic route data with straight-line coordinates
 */
const createFallbackRoute = (origin, destination) => {
  const coords = [[origin.lat, origin.lng], [destination.lat, destination.lng]];
  const dlat = destination.lat - origin.lat;
  const dlng = destination.lng - origin.lng;
  const steps = 100; // Intermediate points for smoother rendering
  
  // Create ~100 points along straight line for smoother visualization
  const polyline = Array.from({ length: steps }, (_, i) => [
    origin.lat + (dlat * i) / steps,
    origin.lng + (dlng * i) / steps,
  ]);
  
  const distance = Math.sqrt(dlat * dlat + dlng * dlng) * 111000; // Rough km to meters
  const duration = (distance / 1389) * 3600; // Assume ~50km/h average

  console.log(`⚠️  Using fallback straight-line route (OSRM unavailable)`);

  return {
    id: `fallback_${Date.now()}`,
    coordinates: polyline,
    distance,
    duration,
    origin,
    destination,
    waypoints: [],
    alternatives: [],
    isFallback: true,
  };
};

/**
 * Decode polyline from OSRM response
 * OSRM returns encoded polylines by default
 * @param {string} encoded - Encoded polyline string
 * @returns {Array} Array of [lat, lng] coordinates
 */
export const decodePolyline = (encoded) => {
  if (!encoded || typeof encoded !== 'string') return [];
  
  const inv = 1.0 / 1e5;
  const decoded = [];
  let previous = [0, 0];
  let i = 0;

  while (i < encoded.length) {
    let ll = [0, 0];
    for (let j = 0; j < 2; j++) {
      let shift = 0;
      let result = 0;
      let byte = 0;
      do {
        byte = encoded.charCodeAt(i++) - 63;
        result |= (byte & 0x1f) << shift;
        shift += 5;
      } while (byte >= 0x20);
      ll[j] = previous[j] + (result & 1 ? ~(result >> 1) : result >> 1);
      previous[j] = ll[j];
    }
    decoded.push([ll[0] * inv, ll[1] * inv]);
  }
  return decoded;
};

/**
 * Get OSRM route between coordinates
 * @param {Object} origin - {lat, lng}
 * @param {Object} destination - {lat, lng}
 * @param {Array} waypoints - Optional intermediate points [{lat, lng}, ...]
 * @param {Object} options - {profile: 'driving'|'walking'|'cycling', alternatives: boolean}
 * @returns {Promise} Route geometry and metadata
 */
/**
 * Fetch with timeout
 */
const fetchWithTimeout = (url, timeoutMs = TIMEOUT_MS) => {
  return Promise.race([
    fetch(url),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error(`Timeout after ${timeoutMs}ms`)), timeoutMs)
    ),
  ]);
};

/**
 * Retry logic for failed requests
 */
const retryAsync = async (fn, attempts = RETRY_ATTEMPTS, delayMs = RETRY_DELAY_MS) => {
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (error) {
      console.warn(`⚠️  Attempt ${i + 1}/${attempts} failed:`, error.message);
      if (i < attempts - 1) {
        await new Promise(resolve => setTimeout(resolve, delayMs * (i + 1)));
      } else {
        throw error;
      }
    }
  }
};

export const getRoute = async (origin, destination, waypoints = [], options = {}) => {
  try {
    if (!origin?.lat || !origin?.lng || !destination?.lat || !destination?.lng) {
      throw new Error('Invalid origin or destination coordinates');
    }

    const { profile = 'driving', alternatives = true } = options;

    // Build coordinate string: origin;waypoints...;destination
    let coordinates = `${origin.lng},${origin.lat}`;
    
    if (waypoints && waypoints.length > 0) {
      waypoints.forEach(wp => {
        coordinates += `;${wp.lng},${wp.lat}`;
      });
    }
    
    coordinates += `;${destination.lng},${destination.lat}`;

    // Build OSRM URL with options
    const url = new URL(`${OSRM_BASE}/${coordinates}`);
    url.searchParams.append('overview', 'full'); // Get full geometry
    url.searchParams.append('alternatives', alternatives ? 'true' : 'false');
    url.searchParams.append('steps', 'true'); // Get turn-by-turn instructions
    url.searchParams.append('annotations', 'duration,distance,speed');

    console.log('🛣️  Requesting route from OSRM (with timeout + retry)...');

    // Use retry logic with timeout for resilience
    const response = await retryAsync(
      () => fetchWithTimeout(url.toString(), TIMEOUT_MS),
      RETRY_ATTEMPTS,
      RETRY_DELAY_MS
    );

    if (!response.ok) {
      throw new Error(`OSRM error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    if (data.code !== 'Ok') {
      throw new Error(`OSRM error: ${data.code}`);
    }

    if (!data.routes || data.routes.length === 0) {
      throw new Error('No route found');
    }

    // Process main route
    const mainRoute = data.routes[0];
    const polyline = decodePolyline(mainRoute.geometry);
    
    const routeData = {
      id: `route_${Date.now()}`, // Unique route ID
      coordinates: polyline,
      distance: mainRoute.distance, // meters
      duration: mainRoute.duration, // seconds
      waypoints: data.waypoints, // Snapped waypoint positions
      legs: mainRoute.legs,
      steps: mainRoute.steps,
      origin,
      destination,
      alternatives: data.routes.slice(1).map((route, idx) => ({
        id: `alt_${idx}`,
        coordinates: decodePolyline(route.geometry),
        distance: route.distance,
        duration: route.duration,
        legs: route.legs,
      })),
      raw: data,
      isFallback: false,
    };

    console.log('✅ Route received:', {
      distance: `${(routeData.distance / 1000).toFixed(2)} km`,
      duration: `${(routeData.duration / 60).toFixed(0)} min`,
      points: polyline.length,
    });

    return routeData;
  } catch (error) {
    console.error('❌ OSRM routing failed:', error.message);
    // Return fallback route so visualization doesn't break
    return createFallbackRoute(origin, destination);
  }
};

/**
 * Get multiple routes (main + alternatives)
 * @param {Object} origin
 * @param {Object} destination
 * @param {Array} waypoints
 * @returns {Promise} Array of routes
 */
export const getRouteAlternatives = async (origin, destination, waypoints = []) => {
  try {
    const routeData = await getRoute(origin, destination, waypoints, { alternatives: true });
    return [
      {
        ...routeData,
        type: 'main',
      },
      ...routeData.alternatives.map(alt => ({
        ...alt,
        type: 'alternative',
        origin,
        destination,
      })),
    ];
  } catch (error) {
    console.error('Error getting alternatives:', error);
    return [];
  }
};

/**
 * Get route matrix (distance/duration between multiple points)
 * Useful for optimization
 * @param {Array} coordinates - [{lat, lng}, ...]
 * @returns {Promise} Distance matrix
 */
export const getMatrix = async (coordinates) => {
  try {
    if (!coordinates || coordinates.length < 2) {
      throw new Error('Need at least 2 coordinates');
    }

    // Format: lng,lat;lng,lat;...
    const coords = coordinates.map(c => `${c.lng},${c.lat}`).join(';');
    const url = `https://router.project-osrm.org/table/v1/driving/${coords}`;

    console.log('📊 Requesting distance matrix from OSRM...');

    const response = await fetch(url);
    const data = await response.json();

    if (data.code !== 'Ok') {
      throw new Error(`Matrix error: ${data.code}`);
    }

    return {
      distances: data.distances, // meters
      durations: data.durations, // seconds
      sources: data.sources,
      destinations: data.destinations,
    };
  } catch (error) {
    console.error('❌ Matrix error:', error);
    throw error;
  }
};

/**
 * Calculate route metrics
 * @param {Object} routeData - Route data from getRoute()
 * @returns {Object} Metrics object
 */
export const calculateMetrics = (routeData) => {
  if (!routeData) return null;

  const distanceKm = routeData.distance / 1000;
  const durationMinutes = routeData.duration / 60;
  const durationHours = durationMinutes / 60;
  const avgSpeed = distanceKm / durationHours;

  // Estimate fuel based on distance and consumption rate
  // Average: 6-8 L/100km for trucks
  const fuelPerKm = 0.07; // 7L/100km
  const estimatedFuel = (distanceKm * fuelPerKm).toFixed(2);

  // Estimate cost
  // Assuming $2.50/km operational cost
  const costPerKm = 2.50;
  const estimatedCost = (distanceKm * costPerKm).toFixed(2);

  return {
    distance: distanceKm,
    distanceFormatted: `${distanceKm.toFixed(2)} km`,
    duration: durationMinutes,
    durationFormatted: formatDuration(durationMinutes),
    durationHours: durationHours.toFixed(2),
    avgSpeed: avgSpeed.toFixed(2),
    estimatedFuel,
    estimatedCost,
    waypoints: routeData.legs?.length || 0,
  };
};

/**
 * Format duration in human-readable format
 * @param {number} minutes
 * @returns {string} Formatted duration
 */
export const formatDuration = (minutes) => {
  if (minutes < 1) return `${Math.round(minutes * 60)}s`;
  if (minutes < 60) return `${Math.round(minutes)}m`;
  
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  return `${hours}h ${mins}m`;
};

/**
 * Get route instructions (turn-by-turn)
 * @param {Object} routeData
 * @returns {Array} Array of instructions
 */
export const getInstructions = (routeData) => {
  if (!routeData?.steps || routeData.steps.length === 0) {
    return [];
  }

  return routeData.steps.map((step, idx) => ({
    id: idx,
    instruction: step.maneuver?.instruction || 'Continue',
    direction: step.maneuver?.type || 'continue',
    distance: (step.distance / 1000).toFixed(2),
    duration: (step.duration / 60).toFixed(1),
    name: step.name || 'Unnamed road',
    bearing: step.bearing_before,
  }));
};

/**
 * Validate if route passes through a polygon (safety check)
 * Simple bounding box check
 * @param {Array} routeCoordinates - [[lat, lng], ...]
 * @param {Array} hazardZones - [{minLat, maxLat, minLng, maxLng}, ...]
 * @returns {Array} Hazards found
 */
export const checkHazards = (routeCoordinates, hazardZones = []) => {
  const hazards = [];

  routeCoordinates.forEach((coord, idx) => {
    hazardZones.forEach(zone => {
      if (
        coord[0] >= zone.minLat &&
        coord[0] <= zone.maxLat &&
        coord[1] >= zone.minLng &&
        coord[1] <= zone.maxLng
      ) {
        hazards.push({
          pointIndex: idx,
          coordinate: coord,
          zone: zone.name || 'Unknown hazard',
          severity: zone.severity || 'medium',
        });
      }
    });
  });

  return hazards;
};

export default {
  getRoute,
  getRouteAlternatives,
  getMatrix,
  calculateMetrics,
  formatDuration,
  getInstructions,
  checkHazards,
  decodePolyline,
};
