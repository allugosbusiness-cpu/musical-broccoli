/**
 * Web Worker for background alert evaluation
 * Prevents UI thread blocking during geometry calculations
 * File: client/Frontend/src/workers/alert-evaluator.worker.js
 *
 * Usage:
 *   const worker = new Worker('alert-evaluator.worker.js');
 *   worker.postMessage({
 *     type: 'evaluate',
 *     locations: [{lat, lng, speed, timestamp}, ...],
 *     route: {id, points: [[lat, lng], ...]},
 *     config: {threshold_m: 50, consensus_count: 3}
 *   });
 *   worker.onmessage = (event) => {
 *     const {alerts, metrics} = event.data;
 *   };
 */

// Configuration
const DEFAULT_CONFIG = {
  threshold_m: 50,
  consensus_count: 3,
  window_seconds: 30
};

// Per-vehicle state
const vehicleState = new Map();

// Metrics
const metrics = {
  evaluations: 0,
  alerts_generated: 0,
  geometry_errors: 0,
  start_time: Date.now()
};

/**
 * Haversine distance (simplified for frontend, no error handling)
 */
function haversineDistance(p1, p2) {
  const [lat1, lng1] = p1;
  const [lat2, lng2] = p2;
  const R = 6371000; // meters

  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Bounding box check (fast prefilter)
 */
function getBoundingBox(polyline) {
  let minLat = Infinity, maxLat = -Infinity;
  let minLng = Infinity, maxLng = -Infinity;

  for (const [lat, lng] of polyline) {
    minLat = Math.min(minLat, lat);
    maxLat = Math.max(maxLat, lat);
    minLng = Math.min(minLng, lng);
    maxLng = Math.max(maxLng, lng);
  }

  return { minLat, maxLat, minLng, maxLng };
}

function isInBoundingBox(point, bbox) {
  const [lat, lng] = point;
  const { minLat, maxLat, minLng, maxLng } = bbox;
  return lat >= minLat && lat <= maxLat && lng >= minLng && lng <= maxLng;
}

/**
 * Point to line segment distance
 */
function pointToSegmentDistance(point, segStart, segEnd) {
  const [px, py] = point;
  const [x1, y1] = segStart;
  const [x2, y2] = segEnd;

  const A = px - x1;
  const B = py - y1;
  const C = x2 - x1;
  const D = y2 - y1;

  const dot = A * C + B * D;
  const lenSq = C * C + D * D;
  let param = -1;

  if (lenSq !== 0) param = dot / lenSq;

  let xx, yy;

  if (param < 0) {
    xx = x1;
    yy = y1;
  } else if (param > 1) {
    xx = x2;
    yy = y2;
  } else {
    xx = x1 + param * C;
    yy = y1 + param * D;
  }

  const dx = px - xx;
  const dy = py - yy;
  return Math.sqrt(dx * dx + dy * dy);
}

/**
 * Point to polyline distance (bounding box → segments)
 */
function pointToPolylineDistance(point, polyline) {
  if (!polyline || polyline.length < 2) return Infinity;

  const bbox = getBoundingBox(polyline);
  if (!isInBoundingBox(point, bbox)) {
    // Rough fallback: distance to nearest point
    let minDist = Infinity;
    for (const p of polyline) {
      const d = haversineDistance(point, p);
      minDist = Math.min(minDist, d);
    }
    return minDist;
  }

  // Check all segments
  let minDist = Infinity;
  for (let i = 0; i < polyline.length - 1; i++) {
    const dist = pointToSegmentDistance(point, polyline[i], polyline[i + 1]);
    minDist = Math.min(minDist, dist);
  }

  return minDist;
}

/**
 * Check if point is off route
 */
function isOffRoute(location, route, config) {
  const point = [location.lat, location.lng];
  const distance = pointToPolylineDistance(point, route.points);

  if (!isFinite(distance)) {
    metrics.geometry_errors++;
    return false;
  }

  return distance > config.threshold_m;
}

/**
 * Evaluate batch of locations
 */
function evaluateBatch(locations, route, config) {
  const alerts = [];

  for (const location of locations) {
    metrics.evaluations++;
    const truckId = location.truck_id;

    // Initialize vehicle state if needed
    if (!vehicleState.has(truckId)) {
      vehicleState.set(truckId, {
        consecutive_off_route: 0,
        last_alert_time: 0,
        cooldown_ms: 0
      });
    }

    const state = vehicleState.get(truckId);
    const now = location.timestamp_ms || Date.now();

    // Check cooldown
    if (state.cooldown_ms > 0 && now < state.last_alert_time + state.cooldown_ms) {
      // Still in cooldown
      continue;
    }

    // Check if off route
    if (route && isOffRoute(location, route, config)) {
      state.consecutive_off_route++;

      if (state.consecutive_off_route >= config.consensus_count) {
        // Alert!
        alerts.push({
          truck_id: truckId,
          type: 'off_route',
          message: `Vehicle off route by ${location.distance_m?.toFixed(0)}m`,
          timestamp: location.timestamp,
          location: { lat: location.lat, lng: location.lng }
        });

        metrics.alerts_generated++;

        // Set cooldown
        state.last_alert_time = now;
        state.cooldown_ms = (config.cooldown_ms || 300000) * 2; // Exponential backoff
        state.consecutive_off_route = 0;
      }
    } else {
      state.consecutive_off_route = 0;
    }
  }

  return alerts;
}

/**
 * Message handler
 */
self.onmessage = function (event) {
  const { type, locations, route, config: userConfig } = event.data;

  if (type === 'evaluate') {
    try {
      const config = { ...DEFAULT_CONFIG, ...userConfig };
      const alerts = evaluateBatch(locations, route, config);

      self.postMessage({
        type: 'result',
        alerts,
        metrics,
        error: null
      });
    } catch (error) {
      self.postMessage({
        type: 'result',
        alerts: [],
        metrics,
        error: error.message
      });
    }
  } else if (type === 'reset') {
    vehicleState.clear();
    self.postMessage({ type: 'reset_ack' });
  } else if (type === 'get_metrics') {
    self.postMessage({
      type: 'metrics',
      data: {
        ...metrics,
        uptime_ms: Date.now() - metrics.start_time,
        vehicles_tracked: vehicleState.size
      }
    });
  }
};

// Indicate worker is ready
self.postMessage({ type: 'ready' });
