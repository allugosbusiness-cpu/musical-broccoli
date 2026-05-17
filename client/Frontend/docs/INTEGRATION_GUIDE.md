# Road-Matched Trail System - Integration Guide

## Quick Start

### 1. Install Dependencies

```bash
npm install leaflet
# Already have: React 18+
```

---

## 2. Basic Setup

### In your main map component:

```javascript
import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import RoadMatchedTrailSystem from './components/RoadMatchedTrailSystem';
import '../styles/trailStyles.css';

export default function FleetMap() {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const [trucks, setTrucks] = React.useState([]);

  // Initialize Leaflet map
  useEffect(() => {
    if (!mapRef.current) return;

    mapInstance.current = L.map(mapRef.current).setView([-17.8252, 31.0335], 7);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
      maxZoom: 19,
    }).addTo(mapInstance.current);

    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove();
      }
    };
  }, []);

  // Load trucks with route data
  useEffect(() => {
    const fetchTrucks = async () => {
      const response = await fetch('/api/trucks/');
      const data = await response.json();
      
      // Trucks must have: id, coordinates, origin_coordinates, destination_coordinates
      setTrucks(data);
    };

    fetchTrucks();
  }, []);

  return (
    <div style={{ height: '100vh' }}>
      <div ref={mapRef} style={{ height: '100%', width: '100%' }} />
      
      <RoadMatchedTrailSystem 
        mapInstance={mapInstance.current} 
        trucks={trucks} 
      />
    </div>
  );
}
```

---

## 3. Truck Data Structure

Each truck object should include:

```javascript
{
  id: 'TRUCK-001',
  plate: 'ZWE-0001',
  driver: 'James Banda',
  coordinates: { lat: -17.85, lng: 31.05 },           // Current position
  origin_coordinates: { lat: -17.8252, lng: 31.0335 }, // Harare
  destination_coordinates: { lat: -20.2811, lng: 28.7578 }, // Bulawayo
  origin: 'Harare Central',
  destination: 'Bulawayo Depot',
  speed: 65,                 // km/h (optional, for display)
  status: 'moving',
  cargo: 'Electronics',
  weight: 2500               // kg
}
```

---

## 4. Handle Real-Time GPS Updates

```javascript
// When truck GPS updates arrive (e.g., via WebSocket)
const handleGpsUpdate = (truckId, lat, lng) => {
  // Update truck in state
  setTrucks(prev => 
    prev.map(t => 
      t.id === truckId 
        ? {...t, coordinates: {lat, lng}}
        : t
    )
  );

  // Trigger trail update via API
  if (window.RoadMatchedTrailAPI) {
    window.RoadMatchedTrailAPI.onGpsUpdate(truckId, lat, lng);
  }
};

// Example WebSocket listener:
// socket.on('truck-gps', ({truckId, lat, lng}) => handleGpsUpdate(truckId, lat, lng));
```

---

## 5. Backend Integration

### Create Truck Color Endpoint

```python
# Django views.py

from django.http import JsonResponse
from .models import Truck
from .utils import generateColorFromTruckId

@api_view(['GET'])
def get_truck_color(request, truck_id):
    """Get assigned color for truck"""
    truck = Truck.objects.get(id=truck_id)
    color = truck.route_color or generateColorFromTruckId(truck_id)
    return JsonResponse({'color': color})

@api_view(['POST'])
def assign_truck_color(request, truck_id):
    """Manually assign color to truck"""
    color = request.data.get('color')
    truck = Truck.objects.get(id=truck_id)
    truck.route_color = color
    truck.save()
    return JsonResponse({'color': color, 'truck_id': truck_id})
```

### Return Coordinates in API

```python
class TruckSerializer(serializers.ModelSerializer):
    coordinates = serializers.SerializerMethodField()
    origin_coordinates = serializers.SerializerMethodField()
    destination_coordinates = serializers.SerializerMethodField()
    
    def get_coordinates(self, obj):
        return {'lat': obj.latitude, 'lng': obj.longitude}
    
    def get_origin_coordinates(self, obj):
        return {'lat': obj.origin_lat, 'lng': obj.origin_lng}
    
    def get_destination_coordinates(self, obj):
        return {'lat': obj.dest_lat, 'lng': obj.dest_lng}
    
    class Meta:
        model = Truck
        fields = ['id', 'plate', 'driver', 'coordinates', 
                  'origin_coordinates', 'destination_coordinates', ...]
```

---

## 6. Advanced Features

### Enable Colorblind Mode

```javascript
// In your UI settings panel
<select onChange={(e) => {
  // Pass colorblindMode to component
  setColorblindMode(e.target.value);
}}>
  <option value="">Normal</option>
  <option value="deuteranopia">Red-Green Colorblind</option>
  <option value="protanopia">Protanopia</option>
  <option value="tritanopia">Tritanopia</option>
</select>
```

### High Contrast Mode

```javascript
<label>
  <input 
    type="checkbox" 
    onChange={(e) => setHighContrast(e.target.checked)}
  />
  High Contrast Mode
</label>
```

### Monitor Cache & Performance

```javascript
// In component
useEffect(() => {
  const timer = setInterval(() => {
    if (window.RoadMatchedTrailAPI) {
      const stats = window.RoadMatchedTrailAPI.getCacheStats();
      console.log('Trail Cache Stats:', stats);
      // Stats: {cachedRoutes, trackedTrucks, pendingReroutes}
    }
  }, 5000);

  return () => clearInterval(timer);
}, []);
```

---

## 7. Configuration

### Customize Constants

In `roadMatchedTrailService.js`:

```javascript
// Increase off-route threshold to 100m
const OFF_ROUTE_THRESHOLD_METERS = 100;

// Increase debounce to 10 seconds
const REROUTE_DEBOUNCE_MS = 10000;

// Cache for 10 minutes instead of 5
const CACHE_MAX_AGE_MS = 600000;
```

### Customize Styling

In `trailStyles.css`:

```css
/* Make trails wider */
.trail-polyline {
  stroke-width: 6 !important; /* Default: 4 */
}

/* Change active trail color schema */
.trail-TRUCK-001 {
  stroke: hsl(220, 85%, 55%) !important; /* Brighter blue */
}

/* Adjust glow intensity */
.trail-shadow {
  opacity: 0.4 !important; /* Default: 0.3 */
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.25)) !important;
}
```

---

## 8. Error Handling

```javascript
// Handle OSRM unavailability
const handleRouteError = async (truck) => {
  console.warn('OSRM unavailable, falling back to local snapping');
  
  // Fallback: Use smart interpolation instead of OSRM
  const smoothPath = smartInterpolate(
    truck.coordinates,
    truck.destination_coordinates,
    50 // intermediate points
  );
  
  // Render smooth trail locally
  renderTrailPolyline(map, smoothPath, {color: '#999', weight: 2});
};
```

---

## 9. Testing

### Run Test Suite

```javascript
// In browser console
import { runAllTests } from './src/__tests__/roadMatchedTrailTests.js';
await runAllTests();
```

### Manual Test Cases

#### Test 1: On-Route
```javascript
// Truck traveling Harare → Mutare, staying on main road
GPS: -17.85, 31.05  → -18.85, 31.8  → -18.95, 32.6
Expected: No off-route alert
```

#### Test 2: Small Deviation
```javascript
// Truck briefly deviates 10-30m (e.g., fuel stop)
GPS deviates 0.0005° (~55m)
Expected: No alert (below 50m threshold)
```

#### Test 3: Major Detour (via Bulawayo)
```javascript
// Truck heading to Harare but detours via Bulawayo first
Origin: Harare (-17.8, 31.0)
Current: Bulawayo (-20.2, 28.7)  ← Major detour west!
Dest: Mutare (-18.9, 32.6)
Expected: Off-route alert + reroute scheduled
Result: New route: Harare → Bulawayo → Mutare
```

#### Test 4: Overlapping Trails
```javascript
// TRUCK-001 (Harare → Mutare) and TRUCK-002 (Mutare → Harare) cross paths
Expected: Both trails rendered, overlapping segments dashed + offset
Visual: Blue solid → Overlapping zone (dashed) → Orange solid
```

#### Test 5: Colorblind Mode
```javascript
// Activate deuteranopia mode
// TRUCK-001 (blue) → #1f77b4 (red-green safe)
// TRUCK-002 (orange) → #ff7f0e (red-green safe)
// Verify visually distinct for colorblind users
```

---

## 10. Performance Optimization

### 1. Lazy Load Trails

```javascript
// Only render trails for visible trucks
const visibleTrucks = trucks.filter(truck => 
  isWithinMapBounds(truck.coordinates, mapBounds)
);

return <RoadMatchedTrailSystem trucks={visibleTrucks} />;
```

### 2. Debounce GPS Updates

```javascript
const [gpsBatch, setGpsBatch] = React.useState({});

const handleGpsUpdate = (truckId, lat, lng) => {
  setGpsBatch(prev => ({...prev, [truckId]: {lat, lng}}));
};

// Batch update every 2 seconds
useEffect(() => {
  const timer = setInterval(() => {
    Object.entries(gpsBatch).forEach(([truckId, coords]) => {
      window.RoadMatchedTrailAPI?.onGpsUpdate(truckId, coords.lat, coords.lng);
    });
    setGpsBatch({});
  }, 2000);

  return () => clearInterval(timer);
}, []);
```

### 3. Clear Expired Trails

```javascript
import { clearExpiredTrails } from './services/roadMatchedTrailService';

useEffect(() => {
  const timer = setInterval(clearExpiredTrails, 30000); // Every 30s
  return () => clearInterval(timer);
}, []);
```

---

## 11. Deployment Checklist

- [ ] Import `trailStyles.css` in main app
- [ ] Ensure truck data includes all required fields
- [ ] Test OSRM connectivity (https://router.project-osrm.org/)
- [ ] Set appropriate `OFF_ROUTE_THRESHOLD_METERS` for your use case
- [ ] Test on 3G/4G network (check timeout settings)
- [ ] Verify colorblind mode on actual colorblind hardware/simulator
- [ ] Load test with 20+ trucks
- [ ] Monitor localStorage quota (color persistence)
- [ ] Set up error boundaries for failed route requests
- [ ] Document truck data API contract for backend team

---

## 12. Troubleshooting

### Trails Not Showing
```javascript
// Check 1: Truck data has coordinates?
console.log(trucks[0]); // Should have origin_coordinates, destination_coordinates

// Check 2: Map initialized?
console.log(mapInstance.current); // Should be L.Map instance

// Check 3: CSS loaded?
document.styleSheets; // Should include trailStyles.css

// Check 4: OSRM reachable?
fetch('https://router.project-osrm.org/route/v1/driving/31.0335,-17.8252;28.7578,-20.2811')
```

### Off-Route Never Triggered
```javascript
// Check threshold is reasonable
const OFF_ROUTE_THRESHOLD_METERS = 50; // or increase to 100

// Manually test
const result = detectOffRoute(geometry, 0, 0); // Far from route
console.log(result); // Should show large distanceOffRoute
```

### Reroute Takes Too Long
```javascript
// Reduce debounce window
REROUTE_DEBOUNCE_MS = 2000; // Instead of 5000

// Or increase OSRM timeout
getRoute(origin, current, dest, {timeout: 15000});
```

---

## 13. Example: Complete GPS Simulator

```javascript
// Simulate GPS updates for testing
function startGpsSimulator(truck, route, speedKmh = 60) {
  const pointDuration = (route.duration / route.geometry.length) * 1000;
  let pointIndex = 0;

  const simulator = setInterval(() => {
    if (pointIndex >= route.geometry.length) {
      clearInterval(simulator);
      console.log(`✅ Simulation complete for ${truck.id}`);
      return;
    }

    const point = route.geometry[pointIndex];
    
    // Update truck position
    console.log(`📍 ${truck.id}: ${point.lat.toFixed(4)}, ${point.lng.toFixed(4)}`);
    
    // Trigger API
    window.RoadMatchedTrailAPI?.onGpsUpdate(truck.id, point.lat, point.lng);
    
    pointIndex++;
  }, pointDuration);

  return simulator;
}

// Usage:
// const route = await getRoute(origin, origin, destination);
// startGpsSimulator(truck, route, 60); // 60 km/h
```

---

## Support & Resources

- **OSRM Docs**: https://project-osrm.org/docs/v5.27.1/api/
- **Leaflet Docs**: https://leafletjs.com/reference/
- **Polyline6 Format**: https://github.com/Project-OSRM/osrm-backend/wiki/Encoding
- **Zimbabwe Coordinates**: Harare (−17.8252°, 31.0335°), Bulawayo (−20.2811°, 28.7578°), Mutare (−18.978°, 32.667°)

---

**Version**: 1.0.0  
**Last Updated**: May 2026
