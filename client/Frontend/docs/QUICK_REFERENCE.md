# Road-Matched Trail System - Quick Reference Card

## 🚀 1-Minute Setup

```javascript
import RoadMatchedTrailSystem from './components/RoadMatchedTrailSystem';

<RoadMatchedTrailSystem mapInstance={map} trucks={truckArray} />
```

## 📋 Truck Data Format

```javascript
{
  id: 'TRUCK-001',
  coordinates: {lat: -17.85, lng: 31.05},           // Current GPS
  origin_coordinates: {lat: -17.8252, lng: 31.0335}, // Harare
  destination_coordinates: {lat: -20.2811, lng: 28.7578}, // Bulawayo
  // Optional but recommended:
  driver: 'James Banda',
  origin: 'Harare Central',
  destination: 'Bulawayo Depot'
}
```

## 🔗 Core Functions

### Get Route
```javascript
const route = await window.RoadMatchedTrailAPI.getRoute(origin, current, destination);
// Returns: {geometry, distance, duration, steps}
```

### Update GPS
```javascript
window.RoadMatchedTrailAPI.onGpsUpdate('TRUCK-001', -17.86, 31.06);
// Automatically checks off-route, triggers reroute if needed
```

### Get Truck Color
```javascript
const color = colorStore.assignColor('TRUCK-001');
// Returns: 'hsl(210, 75%, 50%)' - same every time for same truck
```

### Check Off-Route
```javascript
const {isOffRoute, distanceOffRoute} = detectOffRoute(
  route.geometry, 
  truck.lat, 
  truck.lng, 
  50  // threshold meters
);
```

### Detect Overlap
```javascript
const {isOverlapping, overlapSegments} = detectOverlap(
  route1.geometry, 
  route2.geometry, 
  100  // proximity threshold
);
```

## 🎨 CSS Classes

**Trail Polylines:**
- `.trail-polyline` - Base
- `.trail-polyline.trail-active` - Currently active
- `.trail-polyline.trail-overlapping` - Dashed + offset

**Markers:**
- `.trail-marker-origin` - Purple START
- `.trail-marker-destination` - Pink END
- `.truck-position-marker` - Pulsing truck icon

**Info:**
- `.trail-info-box` - ETA/distance box
- `.reroute-toast` - Notification toast
- `.trail-controls` - Debug controls

**Accessibility:**
- `.trail-colorblind-deuteranopia` - Red-green safe
- `.trail-colorblind-protanopia` - Alternative red-green
- `.trail-colorblind-tritanopia` - Blue-yellow safe
- `.trail-high-contrast` - Enhanced visibility

## ⚙️ Configuration Constants

In `roadMatchedTrailService.js`:

```javascript
OFF_ROUTE_THRESHOLD_METERS = 50       // Deviation threshold
REROUTE_DEBOUNCE_MS = 5000            // Min time between reroutes
CACHE_MAX_AGE_MS = 300000             // 5-minute cache TTL
OSRM_BASE_URL = 'https://router.project-osrm.org/route/v1/driving'
```

## 🧪 Testing

```javascript
// Run all tests
import { runAllTests } from './src/__tests__/roadMatchedTrailTests.js';
await runAllTests();

// Or in browser console:
window.runTrailTests();
```

**Test Scenarios:**
1. On-route travel (no alerts)
2. Small deviation <50m (ignored)
3. Major detour >100m (off-route alert + reroute)
4. Overlapping trails (both visible)
5. Colorblind mode (safe colors)

## 📊 Performance Monitoring

```javascript
const stats = window.RoadMatchedTrailAPI.getCacheStats();
console.log(stats);
// {cachedRoutes: 3, trackedTrucks: 5, pendingReroutes: 0}
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Trails not showing | Check truck has `origin_coordinates` & `destination_coordinates` |
| Off-route never triggers | Increase `OFF_ROUTE_THRESHOLD_METERS` from 50 to 100 |
| Reroute takes too long | Reduce `REROUTE_DEBOUNCE_MS` from 5000 to 2000 |
| OSRM timeout | Increase timeout option: `getRoute(..., {timeout: 15000})` |
| Colors not persisting | Check localStorage enabled; call `colorStore.clearAll()` to reset |
| Colorblind mode not working | Pass `colorblindMode` prop: `setColorblindMode('deuteranopia')` |

## 🌍 Zimbabwe Coordinates

```javascript
Harare: {lat: -17.8252, lng: 31.0335}    // Capital
Bulawayo: {lat: -20.2811, lng: 28.7578}  // South (~440km)
Mutare: {lat: -18.978, lng: 32.667}      // East (~220km)
Ruwa: {lat: -17.7, lng: 30.85}           // NW detour
```

## 🎯 Real-Time GPS Integration

```javascript
// WebSocket example
socket.on('truck-gps', ({truckId, lat, lng}) => {
  window.RoadMatchedTrailAPI.onGpsUpdate(truckId, lat, lng);
});

// Poll example (every 10s)
setInterval(async () => {
  const gpsData = await fetch('/api/trucks/gps').then(r => r.json());
  gpsData.forEach(({id, lat, lng}) => {
    window.RoadMatchedTrailAPI.onGpsUpdate(id, lat, lng);
  });
}, 10000);
```

## 📁 File Structure

```
src/
  services/
    └─ roadMatchedTrailService.js        [OSRM routing, caching]
  utils/
    ├─ truckColorUtils.js               [Color management]
    └─ trailOverlapRenderer.js          [Rendering, overlap]
  components/
    └─ RoadMatchedTrailSystem.jsx       [Main React component]
  styles/
    └─ trailStyles.css                  [Google Maps aesthetics]
  __tests__/
    └─ roadMatchedTrailTests.js         [17 test cases]
docs/
  ├─ ROAD_MATCHED_TRAIL_API.md          [Full API reference]
  ├─ INTEGRATION_GUIDE.md               [Setup & examples]
  └─ IMPLEMENTATION_SUMMARY.md          [Overview & features]
```

## 💾 Color Storage

```javascript
// Auto-assigned on first use
colorStore.assignColor('TRUCK-001');  // Gets hsl(h, 75%, 50%)

// Manual override
colorStore.assignColor('TRUCK-002', '#ff6600');  // Force orange

// Retrieve stored color
const color = colorStore.getColor('TRUCK-001');

// Colorblind mode
const cbColor = getColorblindColor('TRUCK-001', 'deuteranopia');
```

## 🔄 OSRM Request Format

```
https://router.project-osrm.org/route/v1/driving/lng1,lat1;lng2,lat2;lng3,lat3
  ?overview=full
  &geometries=polyline6
  &steps=true

Example:
https://router.project-osrm.org/route/v1/driving/31.0335,-17.8252;31.05,-17.85;28.7578,-20.2811?overview=full&geometries=polyline6&steps=true
```

## 🎬 Animation Classes

```css
/* Trail animations */
.trail-fade-in { animation: trail-fade-in 500ms; }
.trail-highlight { animation: trail-highlight 1.5s; }

/* Truck animation */
.truck-pulse { animation: truck-pulse 2s infinite; }

/* Reroute notification */
.reroute-toast { animation: slideInUp 300ms; }
```

## 🔐 Security Notes

- OSRM public API: No authentication required (respect rate limits)
- localStorage: Client-side color storage (not shared across users)
- GPS data: Sent to OSRM for routing (ensure privacy policy covers)
- Consider self-hosted OSRM for sensitive use cases

## 📞 API Endpoints (Backend Integration)

```python
# Get truck with route data
GET /api/trucks/          # Array of trucks with coordinates

# Assign truck color (optional)
POST /api/trucks/{id}/color/   # {color: '#ff6600'}

# Log reroute event (optional)
POST /api/trucks/{id}/reroute/ # {reason: 'off_route', distance_off: 50}

# Get cache stats (debug)
GET /api/trails/cache-stats/   # {cachedRoutes, trackedTrucks, pendingReroutes}
```

## 🎓 Quick Examples

### Highlight a Truck's Route
```javascript
window.RoadMatchedTrailAPI.getTrailState('TRUCK-001');
// Returns: {route, offRoute, lastUpdated, ...}
```

### Simulate GPS Updates
```javascript
for (let i = 0; i < route.geometry.length; i++) {
  const point = route.geometry[i];
  setTimeout(() => {
    window.RoadMatchedTrailAPI.onGpsUpdate('TRUCK-001', point.lat, point.lng);
  }, i * 100);
}
```

### Enable High Contrast for Accessibility
```javascript
// In component - add checkbox to state
const [highContrast, setHighContrast] = useState(false);

// Apply class
<div className={highContrast ? 'trail-high-contrast' : ''}>
  <RoadMatchedTrailSystem ... />
</div>
```

### Format ETA for Display
```javascript
function formatETA(seconds) {
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.round(seconds / 60);
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  const remMins = mins % 60;
  return `${hours}h ${remMins}m`;
}

const eta = formatETA(route.duration); // "2h 15m"
```

---

**💡 Pro Tips:**
- Use `OFF_ROUTE_THRESHOLD_METERS = 100` for urban areas (more forgiveness)
- Set `REROUTE_DEBOUNCE_MS = 10000` for highways (less jitter sensitivity)
- Cache OSRM responses for 10+ minutes in high-traffic scenarios
- Batch GPS updates every 2-5 seconds to reduce API calls
- Test with Zimbabwe data before production deployment

**📖 For detailed info, see:**
- API Reference: [ROAD_MATCHED_TRAIL_API.md](./ROAD_MATCHED_TRAIL_API.md)
- Integration: [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)
- Summary: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)

---

**Version**: 1.0.0 | **Status**: ✅ Production Ready
