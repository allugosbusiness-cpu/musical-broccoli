# Road-Matched Trail System - API Reference

## Overview

A production-ready road-matched trail visualization system for React + Leaflet fleet tracking apps. Features OSRM integration, off-route detection, smart rerouting, overlap handling, and Google Maps-style visuals.

---

## Core Services

### 1. `roadMatchedTrailService.js`

Main routing and trail management logic.

#### `getRoute(origin, current, destination, options?)`

Requests a three-waypoint route from OSRM and caches results.

**Parameters:**
- `origin` {Object}: Starting location `{lat, lng}`
- `current` {Object}: Current truck position `{lat, lng}`
- `destination` {Object}: Target location `{lat, lng}`
- `options` {Object, optional}:
  - `useCache` {boolean}: Use cached responses (default: true)
  - `timeout` {number}: Request timeout in ms (default: 10000)

**Returns:** Promise<Route>
```javascript
{
  geometry: [{lat, lng}, ...],      // Decoded polyline6 points
  steps: Array,                      // Route legs with turn-by-turn
  distance: number,                  // Total distance in meters
  duration: number,                  // Total duration in seconds
  via: {lat, lng},                   // Middle waypoint (current position)
  requestedAt: string                // ISO timestamp
}
```

**Example:**
```javascript
const route = await getRoute(
  { lat: -17.8252, lng: 31.0335 },   // Harare
  { lat: -17.85, lng: 31.05 },       // Current
  { lat: -20.2811, lng: 28.7578 }    // Bulawayo
);

console.log(`Distance: ${route.distance / 1000} km`);
console.log(`Duration: ${route.duration / 60} minutes`);
```

---

#### `detectOffRoute(routeGeometry, gpsLat, gpsLng, thresholdMeters?)`

Checks if truck has deviated from active route.

**Parameters:**
- `routeGeometry` {Array}: Route polyline `[{lat, lng}, ...]`
- `gpsLat` {number}: Current GPS latitude
- `gpsLng` {number}: Current GPS longitude
- `thresholdMeters` {number, optional}: Off-route threshold (default: 50m)

**Returns:**
```javascript
{
  isOffRoute: boolean,                // Deviation exceeds threshold?
  distanceOffRoute: number,           // Distance in meters
  nearestPoint: {lat, lng}            // Closest point on route
}
```

**Example:**
```javascript
const offRouteCheck = detectOffRoute(
  route.geometry,
  truck.lat,
  truck.lng,
  50  // 50m threshold
);

if (offRouteCheck.isOffRoute) {
  console.log(`⚠️ Off route by ${offRouteCheck.distanceOffRoute.toFixed(0)}m`);
  // Trigger reroute
}
```

---

#### `scheduleReroute(truckId, origin, current, destination, onReroute, debounceMs?)`

Schedules a debounced reroute request (prevents excessive OSRM calls).

**Parameters:**
- `truckId` {string}: Truck identifier
- `origin` {Object}: Starting location
- `current` {Object}: Current position
- `destination` {Object}: Target location
- `onReroute` {Function}: Callback: `(truckId, newRoute) => void`
- `debounceMs` {number, optional}: Debounce window (default: 5000ms)

**Example:**
```javascript
scheduleReroute(
  'TRUCK-001',
  harareCoords,
  truckCurrentPos,
  mutareCoords,
  (truckId, newRoute) => {
    console.log(`✅ Reroute complete for ${truckId}`);
    updateTrailDisplay(truckId, newRoute);
  },
  5000  // Minimum 5s between reroute requests
);
```

---

#### `calculateDistance(lat1, lng1, lat2, lng2)`

Haversine formula for great-circle distance.

**Returns:** number (meters)

**Example:**
```javascript
const dist = calculateDistance(-17.8, 31.0, -18.9, 32.6);
console.log(`${(dist / 1000).toFixed(1)} km`);  // ~185.2 km
```

---

#### `updateTrailState(truckId, trailData)`

Store trail state (route, layers, off-route flag, etc.) for a truck.

**Parameters:**
- `truckId` {string}
- `trailData` {Object}: Any trail metadata

**Example:**
```javascript
updateTrailState('TRUCK-001', {
  route: routeObject,
  offRoute: false,
  lastUpdate: Date.now(),
});
```

---

#### `getTrailState(truckId)`

Retrieve stored trail state for a truck.

**Returns:** Object | null

---

#### `getCacheStats()`

Monitor cache performance.

**Returns:**
```javascript
{
  cachedRoutes: number,    // Count of cached OSRM responses
  trackedTrucks: number,   // Trucks in trail state
  pendingReroutes: number  // Scheduled reroute timers
}
```

---

### 2. `truckColorUtils.js`

Color assignment and persistence.

#### `generateColorFromTruckId(truckId)`

Deterministic HSL color from truck ID (MD5-style hash).

**Returns:** string (e.g., `"hsl(210, 75%, 50%)"`)

**Example:**
```javascript
const color = generateColorFromTruckId('TRUCK-001');
// Returns: "hsl(210, 75%, 50%)" (always same for same ID)
```

---

#### `hslToRgb(hslString)`

Convert HSL to hex RGB.

**Parameters:** `"hsl(h, s%, l%)"`

**Returns:** string (e.g., `"#0066cc"`)

---

#### `getComplementaryColor(hslString)`

Generate complementary color for overlap visualization.

**Returns:** string (HSL 180° rotated hue)

---

#### `getColorblindColor(truckId, mode?)`

Accessibility-friendly colors for color-blind drivers.

**Parameters:**
- `truckId` {string}
- `mode` {string}: 'deuteranopia' (default), 'protanopia', 'tritanopia'

**Returns:** string (hex color)

**Example:**
```javascript
const color = getColorblindColor('TRUCK-001', 'deuteranopia');
// Red-green colorblind safe palette
```

---

#### `colorStore.assignColor(truckId, color?)`

Assign and persist truck color (localStorage).

**Parameters:**
- `truckId` {string}
- `color` {string, optional}: Override generated color

**Returns:** string (assigned color)

**Example:**
```javascript
colorStore.assignColor('TRUCK-001');  // Auto-generate
colorStore.assignColor('TRUCK-002', '#ff6600');  // Custom
```

---

#### `getTrailStyle(truckId, options?)`

Generate Leaflet polyline style options.

**Parameters:**
- `truckId` {string}
- `options` {Object, optional}:
  - `color` {string}: Override color
  - `isActive` {boolean}: Active (thicker) or inactive (thin)
  - `isOverlapping` {boolean}: Use dashed pattern
  - `colorblindMode` {string}: 'deuteranopia' | 'protanopia' | 'tritanopia'
  - `width` {number}: Stroke weight

**Returns:** Object (Leaflet polyline style)

**Example:**
```javascript
const style = getTrailStyle('TRUCK-001', {
  isActive: true,
  isOverlapping: false,
  colorblindMode: null,
  width: 4
});
// Returns: {color: '...', weight: 4, opacity: 0.85, ...}
```

---

### 3. `trailOverlapRenderer.js`

Overlap detection and visual rendering.

#### `detectOverlap(geometry1, geometry2, proximityThresholdMeters?)`

Check if two polylines overlap or are very close.

**Parameters:**
- `geometry1` {Array}: Polyline points
- `geometry2` {Array}: Polyline points
- `proximityThresholdMeters` {number}: Distance considered "overlapping" (default: 100m)

**Returns:**
```javascript
{
  isOverlapping: boolean,         // Any overlap detected?
  overlapSegments: Array,         // Overlapping point indices
  proximityScore: number          // Average proximity distance
}
```

**Example:**
```javascript
const overlap = detectOverlap(route1.geometry, route2.geometry, 50);

if (overlap.isOverlapping) {
  console.log(`🔗 ${overlap.overlapSegments.length} overlapping segments`);
  // Render with offset/dashed pattern
}
```

---

#### `renderTrailPolyline(mapInstance, geometry, styleOptions)`

Render Leaflet polyline with shadow effect.

**Parameters:**
- `mapInstance` {L.Map}
- `geometry` {Array}: Route points
- `styleOptions` {Object}:
  - `color` {string}
  - `weight` {number}
  - `opacity` {number}
  - `dashArray` {string}: e.g., "5, 5"
  - `isOverlapping` {boolean}
  - `classNameSuffix` {string}

**Returns:**
```javascript
{
  polyline: L.Polyline,   // Main polyline layer
  shadow: L.Polyline      // Shadow/glow layer
}
```

**Example:**
```javascript
const { polyline, shadow } = renderTrailPolyline(
  map,
  route.geometry,
  {
    color: '#0066cc',
    weight: 4,
    opacity: 0.85,
    isOverlapping: false
  }
);

// Both automatically added to map
```

---

#### `createOverlapAwareTrail(mapInstance, primaryTrailId, primaryGeometry, primaryStyle, overlappingTrails?)`

Render primary trail + overlapping trails with offsets and dashed patterns.

**Parameters:**
- `mapInstance` {L.Map}
- `primaryTrailId` {string}
- `primaryGeometry` {Array}
- `primaryStyle` {Object}
- `overlappingTrails` {Array, optional}:
  - Each element: `{truckId, geometry, color, overlapDetection}`

**Returns:** L.FeatureGroup (all trail layers grouped)

**Example:**
```javascript
const trailGroup = createOverlapAwareTrail(
  map,
  'TRUCK-001',
  route1.geometry,
  {color: '#0066cc', weight: 4},
  [
    {
      truckId: 'TRUCK-002',
      geometry: route2.geometry,
      color: '#ff6600',
      overlapDetection: {isOverlapping: true, ...}
    }
  ]
);

// Primary trail solid blue, overlap trail dashed orange (offset)
```

---

#### `animateTrailTransition(oldPolyline, newPolyline, durationMs?)`

Smooth fade crossfade during reroute.

**Parameters:**
- `oldPolyline` {L.Polyline}
- `newPolyline` {L.Polyline}
- `durationMs` {number}: Transition duration (default: 800ms)

**Example:**
```javascript
animateTrailTransition(oldTrail, newTrail, 800);
// Old trail fades out, new trail fades in over 0.8 seconds
```

---

## React Component

### `RoadMatchedTrailSystem.jsx`

Main React component wrapping the entire system.

**Props:**
- `mapInstance` {L.Map}: Leaflet map reference
- `trucks` {Array}: Truck objects with coordinates and route info

**Features:**
- Raw GPS debug toggle
- High-contrast mode
- Colorblind accessibility
- ETA/distance display
- Reroute toast notifications

**Example Usage:**
```javascript
import RoadMatchedTrailSystem from './components/RoadMatchedTrailSystem';

<RoadMatchedTrailSystem
  mapInstance={mapRef.current}
  trucks={truckList}
/>
```

---

## Global API

After component renders, access via `window.RoadMatchedTrailAPI`:

```javascript
// Update GPS position
window.RoadMatchedTrailAPI.onGpsUpdate('TRUCK-001', -17.85, 31.05);

// Manual route request
const route = await window.RoadMatchedTrailAPI.getRoute(origin, current, dest);

// Get trail state
const state = window.RoadMatchedTrailAPI.getTrailState('TRUCK-001');

// Get cache stats
console.log(window.RoadMatchedTrailAPI.getCacheStats());
```

---

## CSS Classes

### Trail Polylines
- `.trail-polyline` - Base style
- `.trail-polyline.trail-active` - Active route
- `.trail-polyline.trail-inactive` - Historical
- `.trail-polyline.trail-overlapping` - Overlapping (dashed)

### Truck Markers
- `.trail-marker-origin` - Purple gradient START marker
- `.trail-marker-destination` - Pink gradient END marker
- `.truck-position-marker` - Current position with pulse animation

### Info & Controls
- `.trail-info-box` - ETA/distance box
- `.reroute-toast` - Notification toast
- `.trail-controls` - Debug/accessibility controls

### Colorblind Modes
- `.trail-colorblind-deuteranopia` - Red-green colorblind
- `.trail-colorblind-protanopia` - Red-green (variant)
- `.trail-colorblind-tritanopia` - Blue-yellow colorblind

---

## Configuration

### Constants (roadMatchedTrailService.js)

```javascript
OSRM_BASE_URL              // https://router.project-osrm.org/...
REROUTE_DEBOUNCE_MS        // 5000 (5 seconds)
OFF_ROUTE_THRESHOLD_METERS // 50 meters
CACHE_MAX_AGE_MS           // 300000 (5 minutes)
```

### trailRendererConfig

```javascript
google_maps_style: {
  lineCap: 'round',
  lineJoin: 'round',
  shadowBlur: 4,
  shadowColor: 'rgba(0, 0, 0, 0.2)'
}

overlap: {
  proximityThresholdMeters: 100,
  minOverlapSegments: 3
}

animation: {
  reroute_transition_ms: 800,
  trail_fade_in_ms: 500
}

rendering: {
  active_trail_width: 4,
  inactive_trail_width: 2,
  base_opacity: 0.85,
  overlap_opacity: 0.6
}
```

---

## Testing

Run tests in browser console:

```javascript
// Import test suite
import { runAllTests } from './src/__tests__/roadMatchedTrailTests.js';

// Run all tests
await runAllTests();
```

**Test Coverage:**
- ✅ OSRM routing & caching
- ✅ Off-route detection (on-route, small deviation, large deviation)
- ✅ Trail overlap detection & rendering
- ✅ Color management & persistence
- ✅ Real-world scenarios (Harare ↔ Mutare, Bulawayo)

---

## Performance Tips

1. **Cache Responses**: Identical waypoint triples return cached results instantly
2. **Debounce Reroutes**: 5-10s window prevents OSRM rate-limit issues
3. **Cleanup Trails**: Expired trails automatically removed after `preserveHistoricalMs`
4. **Limit Trucks**: Overlap detection O(n²) – optimize for 5-20 trucks
5. **CSS Animations**: Use `.trail-fade-in` class for smooth transitions

---

## Troubleshooting

### OSRM Requests Timeout
- Increase `timeout` option (default 10s)
- Check OSRM public API availability
- Fallback to local snapping via `getRoute()` returning null

### Off-Route False Positives
- Increase `OFF_ROUTE_THRESHOLD_METERS` (adjust from 50m)
- OSRM geometry may snap to nearby roads; verify GPS accuracy

### Color Persistence Not Working
- Check `localStorage` enabled
- Call `colorStore.clearAll()` to reset
- Manually pass colors via `assignColor(truckId, customColor)`

### Overlapping Trails Not Visible
- Ensure `detectOverlap()` proximity threshold matches trail spacing
- Increase `proximityThresholdMeters` if trails are 100m+ apart
- Check CSS z-index and opacity settings

---

## License & Credits

- OSRM: Open Source Routing Machine (https://project-osrm.org/)
- Leaflet: Interactive maps (https://leafletjs.com/)
- Polyline6: Format by Google Maps

---

**Version**: 1.0.0  
**Last Updated**: May 2026
