/**
 * Trail Overlap Detector & Renderer
 * Handles visual overlap detection and rendering with offset/dashed patterns
 */

import { calculateDistance } from '../services/roadMatchedTrailService.js';

/**
 * Check if two polylines are overlapping or very close
 * @param {Array} geometry1 - Polyline points [{lat, lng}, ...]
 * @param {Array} geometry2 - Polyline points [{lat, lng}, ...]
 * @param {number} proximityThresholdMeters - Distance considered "overlapping"
 * @returns {Object} {isOverlapping, overlapSegments, proximityScore}
 */
export function detectOverlap(geometry1, geometry2, proximityThresholdMeters = 100) {
  if (!geometry1 || !geometry2 || geometry1.length < 2 || geometry2.length < 2) {
    return { isOverlapping: false, overlapSegments: [], proximityScore: 0 };
  }

  const overlapSegments = [];
  let totalProximity = 0;
  let proximityCount = 0;

  // Check each point in geometry1 against all points in geometry2
  geometry1.forEach((point1, idx1) => {
    let minDist = Infinity;

    geometry2.forEach((point2) => {
      const dist = calculateDistance(
        point1.lat,
        point1.lng,
        point2.lat,
        point2.lng
      );

      if (dist < minDist) {
        minDist = dist;
      }
    });

    if (minDist <= proximityThresholdMeters) {
      overlapSegments.push({
        index: idx1,
        point: point1,
        distance: minDist,
      });
      totalProximity += minDist;
      proximityCount++;
    }
  });

  const isOverlapping = overlapSegments.length > 0;
  const proximityScore = proximityCount > 0 ? totalProximity / proximityCount : Infinity;

  return {
    isOverlapping,
    overlapSegments,
    proximityScore,
  };
}

/**
 * Compute visual offset for overlapping trails
 * Returns offset in degrees (roughly)
 */
export function computeOverlapOffset(overlapIndex, totalOverlaps = 1) {
  // Calculate offset as fraction of degree
  // At equator, 1 degree ≈ 111km = 111000m
  // Offset 10-20 pixels typically
  const pixelOffsetMeters = 15;
  const offsetDegrees = pixelOffsetMeters / 111000;

  // Spread overlaps in a pattern
  const pattern = [0, offsetDegrees, -offsetDegrees, offsetDegrees * 2, -offsetDegrees * 2];
  return pattern[overlapIndex % pattern.length];
}

/**
 * Apply offset to polyline geometry
 */
export function offsetPolyline(geometry, latOffset = 0, lngOffset = 0) {
  return geometry.map((point) => ({
    lat: point.lat + latOffset,
    lng: point.lng + lngOffset,
  }));
}

/**
 * Render trail in Leaflet with proper styling
 */
export function renderTrailPolyline(mapInstance, geometry, styleOptions) {
  if (!geometry || geometry.length < 2 || !window.L) {
    return null;
  }

  const {
    color = '#0066cc',
    weight = 4,
    opacity = 0.85,
    dashArray = null,
    isOverlapping = false,
    classNameSuffix = '',
  } = styleOptions;

  const latlngs = geometry.map((p) => [p.lat, p.lng]);

  const polylineOptions = {
    color,
    weight,
    opacity,
    lineCap: 'round',
    lineJoin: 'round',
    dashArray,
    className: `trail-polyline${isOverlapping ? ' trail-overlapping' : ''}${classNameSuffix}`,
    // Interactive popup
    bubblingMouseEvents: true,
  };

  // Create polyline with glow effect (using shadow)
  const polyline = window.L.polyline(latlngs, {
    ...polylineOptions,
    // Shadow effect: duplicate polyline underneath
  });

  // Add shadow/glow effect
  const shadow = window.L.polyline(latlngs, {
    color: 'rgba(255, 255, 255, 0.3)',
    weight: weight + 6,
    opacity: 0.3,
    lineCap: 'round',
    lineJoin: 'round',
    dashArray,
    className: 'trail-shadow',
    interactive: false,
  });

  // Add to map
  if (mapInstance) {
    shadow.addTo(mapInstance);
    polyline.addTo(mapInstance);
  }

  return { polyline, shadow };
}

/**
 * Create overlap-aware trail rendering group
 */
export function createOverlapAwareTrail(
  mapInstance,
  primaryTrailId,
  primaryGeometry,
  primaryStyle,
  overlappingTrails = []
) {
  if (!window.L) return null;

  const group = window.L.featureGroup();

  // Render primary trail
  const primary = renderTrailPolyline(mapInstance, primaryGeometry, {
    ...primaryStyle,
    isOverlapping: overlappingTrails.length > 0,
    classNameSuffix: `-primary`,
  });

  if (primary) {
    group.addLayer(primary.shadow);
    group.addLayer(primary.polyline);
  }

  // Render overlapping trails with offset/dashed patterns
  overlappingTrails.forEach((overlappingTrail, index) => {
    const { truckId, geometry, color, overlapDetection } = overlappingTrail;

    // Compute offset for visual distinction
    const offset = computeOverlapOffset(index, overlappingTrails.length);
    const offsetGeometry = offsetPolyline(geometry, offset * 0.5, offset * 0.7);

    const overlappingStyle = {
      color,
      weight: 3,
      opacity: 0.6,
      dashArray: '4, 4', // Dashed pattern for overlap
      isOverlapping: true,
      classNameSuffix: `-overlap-${index}`,
    };

    const overlapping = renderTrailPolyline(mapInstance, offsetGeometry, overlappingStyle);
    if (overlapping) {
      group.addLayer(overlapping.shadow);
      group.addLayer(overlapping.polyline);
    }
  });

  return group;
}

/**
 * Update trail when reroute occurs (smooth splice animation)
 */
export function animateTrailTransition(oldPolyline, newPolyline, durationMs = 800) {
  if (!oldPolyline || !newPolyline) return;

  // Fade out old, fade in new
  let progress = 0;
  const startTime = Date.now();

  const animate = () => {
    const elapsed = Date.now() - startTime;
    progress = Math.min(elapsed / durationMs, 1);

    // Crossfade opacity
    if (oldPolyline) {
      oldPolyline.setStyle({ opacity: 0.85 * (1 - progress) });
    }
    if (newPolyline) {
      newPolyline.setStyle({ opacity: 0.85 * progress });
    }

    if (progress < 1) {
      requestAnimationFrame(animate);
    }
  };

  animate();
}

/**
 * Trail renderer configuration
 */
export const trailRendererConfig = {
  // Visual styling
  google_maps_style: {
    lineCap: 'round',
    lineJoin: 'round',
    shadowBlur: 4,
    shadowColor: 'rgba(0, 0, 0, 0.2)',
  },

  // Overlap detection
  overlap: {
    proximityThresholdMeters: 100,
    minOverlapSegments: 3,
  },

  // Animation
  animation: {
    reroute_transition_ms: 800,
    trail_fade_in_ms: 500,
  },

  // Rendering
  rendering: {
    active_trail_width: 4,
    inactive_trail_width: 2,
    overlap_trail_width: 3,
    base_opacity: 0.85,
    overlap_opacity: 0.6,
    shadow_opacity: 0.3,
  },
};

/**
 * Polyline with gradient effect (canvas-based)
 * For Google Maps aesthetic
 */
export function createGradientPolyline(geometry, startColor, endColor) {
  // This would be used with canvas rendering or SVG overlays
  // Returns style configuration for gradual color change along polyline

  const points = geometry.length;
  const gradientStops = [];

  for (let i = 0; i < points; i++) {
    const ratio = i / Math.max(points - 1, 1);

    // Interpolate between start and end color
    const r1 = parseInt(startColor.slice(1, 3), 16);
    const g1 = parseInt(startColor.slice(3, 5), 16);
    const b1 = parseInt(startColor.slice(5, 7), 16);

    const r2 = parseInt(endColor.slice(1, 3), 16);
    const g2 = parseInt(endColor.slice(3, 5), 16);
    const b2 = parseInt(endColor.slice(5, 7), 16);

    const r = Math.round(r1 + (r2 - r1) * ratio);
    const g = Math.round(g1 + (g2 - g1) * ratio);
    const b = Math.round(b1 + (b2 - b1) * ratio);

    gradientStops.push({
      index: i,
      color: `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`,
    });
  }

  return gradientStops;
}

export default {
  detectOverlap,
  computeOverlapOffset,
  offsetPolyline,
  renderTrailPolyline,
  createOverlapAwareTrail,
  animateTrailTransition,
  createGradientPolyline,
  trailRendererConfig,
};
