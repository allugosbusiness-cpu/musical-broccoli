# 🎯 Coordinate Tracking System - Accurate Mobile→Backend→Web Flow

## System Overview

This document defines the **exact coordinate flow** from mobile app to web dashboard with comprehensive verification points.

---

## 1️⃣ MOBILE APP: GPS CAPTURE

### Location Source: `mobile/src/services/rateLimitedTracker.ts`

```
┌─────────────────────────────────────────┐
│  GPS CAPTURE (Every 5 seconds)          │
├─────────────────────────────────────────┤
│  Location: expo-location                │
│  Accuracy: ±5-10 meters                 │
│  Sample Format:                         │
│  {                                      │
│    lat: -18.976323 (MUST BE NEGATIVE)   │
│    lon: 32.683646  (MUST BE POSITIVE)   │
│    accuracy: 8.5                        │
│    altitude: 1520.0                     │
│    speed: 45.5 km/h                     │
│    timestamp: 1683961800000             │
│  }                                      │
└─────────────────────────────────────────┘
```

**REQUIREMENT**: 
- ✅ Latitude MUST be -18 to -18.99 (Zimbabwe range)
- ✅ Longitude MUST be 25 to 35 (Zimbabwe range)
- ✅ Timestamp MUST be milliseconds since epoch

---

## 2️⃣ MOBILE → BACKEND: API CALL

### Endpoint: `POST /api/v1/mobile/location-update/`

**Backend File**: `server/api/mobile_endpoints.py` (Lines 140-200)

**Request Payload**:
```json
{
  "driver_id": "550e8400-e29b-41d4-a716-446655440000",
  "latitude": -18.976323,
  "longitude": 32.683646,
  "speed": 45.5,
  "accuracy": 8.5,
  "altitude": 1520.0,
  "timestamp": 1683961800000
}
```

**VERIFICATION POINTS**:
1. ✅ `driver_id` exists in database
2. ✅ `latitude` is float and within Zimbabwe bounds
3. ✅ `longitude` is float and within Zimbabwe bounds
4. ✅ `speed` is float >= 0
5. ✅ `timestamp` is valid milliseconds

**Code Path**:
```python
@api_view(['POST'])
def mobile_location_update(request):
    driver_id = request.data.get('driver_id')
    latitude = request.data.get('latitude')      # ← EXTRACT
    longitude = request.data.get('longitude')    # ← EXTRACT
    speed = request.data.get('speed', 0)
    accuracy = request.data.get('accuracy', 0)
    
    # Get driver
    driver = FleetDriver.objects.get(id=driver_id)
    
    # ✅ UPDATE 1: Driver location
    driver.latitude = latitude
    driver.longitude = longitude
    driver.save()
    
    # ✅ UPDATE 2: Truck location (CRITICAL FOR WEB APP)
    if driver.truck:
        driver.truck.last_latitude = float(latitude)      # ← SAVE TO TRUCK
        driver.truck.last_longitude = float(longitude)    # ← SAVE TO TRUCK
        driver.truck.current_location = {
            'lat': float(latitude),
            'lng': float(longitude),
            'timestamp': timezone.now().isoformat()
        }
        driver.truck.save()
    
    # ✅ UPDATE 3: Location history
    TruckLocation.objects.create(
        truck=driver.truck,
        driver=driver,
        latitude=float(latitude),         # ← AUDIT TRAIL
        longitude=float(longitude),       # ← AUDIT TRAIL
        timestamp=...
    )
```

---

## 3️⃣ BACKEND: DATABASE STORAGE

### Tables Updated

**Table 1: `FleetDriver`**
```
id: 550e8400-e29b-41d4-a716-446655440000
latitude: -18.976323        ← STORED
longitude: 32.683646        ← STORED
updated_at: 2026-05-14T10:20:00Z
```

**Table 2: `FleetTruck` (CRITICAL FOR WEB APP)**
```
id: 6f91a80d-eecd-47c5-a4ac-0b546b9cb473
truck_identifier: SCANNER_TEST
plate: ZWE-TEST-1
last_latitude: -18.976323         ← STORED (WEB READS THIS)
last_longitude: 32.683646        ← STORED (WEB READS THIS)
current_location: {               ← STORED (WEB READS THIS)
  "lat": -18.976323,
  "lng": 32.683646,
  "timestamp": "2026-05-14T10:20:00Z"
}
```

**Table 3: `TruckLocation` (Audit Trail)**
```
id: auto
truck_id: 6f91a80d-eecd-47c5-a4ac-0b546b9cb473
driver_id: 550e8400-e29b-41d4-a716-446655440000
latitude: -18.976323          ← AUDIT TRAIL
longitude: 32.683646         ← AUDIT TRAIL
speed: 45.5
accuracy: 8.5
timestamp: 2026-05-14T10:20:00Z
```

---

## 4️⃣ BACKEND → WEB: API FETCH

### Endpoint: `GET /api/v1/dashboard/trucks/`

**Response Format**:
```json
[
  {
    "id": "6f91a80d-eecd-47c5-a4ac-0b546b9cb473",
    "truck_identifier": "SCANNER_TEST",
    "plate": "ZWE-TEST-1",
    "latitude": -18.976323,           ← ✅ FROM FleetTruck.last_latitude
    "longitude": 32.683646,           ← ✅ FROM FleetTruck.last_longitude
    "location": {
      "lat": -18.976323,
      "lon": 32.683646
    },
    "status": "idle",
    "fuel_consumed_liters": 84.52,
    "distance_travelled_km": 1056.622
  },
  ...
]
```

---

## 5️⃣ WEB APP: MAP DISPLAY

### Component: `client/Frontend/src/components/GlobalMap.jsx`

**Data Transformation**:
```javascript
const transformedTrucks = await Promise.all(
  trucksArray.map(async (truck, index) => {
    // Extract coordinates from backend response
    let coordLat = truck.latitude;       // ← READ: -18.976323
    let coordLon = truck.longitude;      // ← READ: 32.683646
    
    // Priority: mission location > truck coordinates
    if (truck.location) {
      if (truck.location.lat !== undefined) {
        coordLat = truck.location.lat;
      }
      if (truck.location.lon !== undefined) {
        coordLon = truck.location.lon;
      }
    }
    
    return {
      id: truck.id,
      identifier: truck.truck_identifier,
      latitude: coordLat,               // ← USE FOR MAP
      longitude: coordLon,              // ← USE FOR MAP
      location_name: await reverseGeocode(coordLat, coordLon)
    };
  })
);
```

**Marker Rendering**:
```javascript
const addTruckMarker = (truck) => {
  const markerLat = truck.latitude;     // ← -18.976323
  const markerLon = truck.longitude;    // ← 32.683646
  
  // Create marker at exact coordinates
  const marker = L.marker([markerLat, markerLon], { icon: customIcon })
    .addTo(markerClusterGroup.current);
  
  // Marker label shows truck name
  // Icon appears at: [-18.976323, 32.683646]
};
```

**Clustering** (Handles overlapping trucks):
```javascript
// If 4 trucks at same location, they cluster together
// Clicking cluster expands to show individual trucks
markerClusterGroup.current = L.markerClusterGroup({
  maxClusterRadius: 60,
  iconCreateFunction: (cluster) => {
    return L.divIcon({
      html: `<div>Cluster: ${cluster.getChildCount()} trucks</div>`
    });
  }
});
```

---

## 🔍 VERIFICATION CHECKLIST

### Step 1: Mobile App Sending

```bash
# Check: Is mobile sending correct coordinates?
✅ Open mobile app in Expo Go
✅ Scan QR for SCANNER_TEST truck
✅ Check Expo Metro console for logs:
   "📍 Location update: -18.976323, 32.683646"
✅ Speed shows actual speed (not 0)
```

### Step 2: Backend Receiving

```bash
# Check: Are coordinates saved to database?
python
>>> from api.models_v2 import FleetTruck
>>> truck = FleetTruck.objects.get(truck_identifier='SCANNER_TEST')
>>> print(f"Latitude: {truck.last_latitude}")
>>> print(f"Longitude: {truck.last_longitude}")
>>> print(f"Current Location: {truck.current_location}")

# EXPECTED OUTPUT:
# Latitude: -18.976323
# Longitude: 32.683646
# Current Location: {'lat': -18.976323, 'lng': 32.683646, ...}
```

### Step 3: Backend API Response

```bash
# Check: Does dashboard API return correct coordinates?
curl -s "https://pulsetrack-back.onrender.com/api/v1/dashboard/trucks/?search=SCANNER_TEST" \
  | python -m json.tool | grep -A 10 "latitude\|longitude"

# EXPECTED OUTPUT:
# "latitude": -18.976323,
# "longitude": 32.683646,
```

### Step 4: Web App Display

```bash
# Check: Does web dashboard show truck icon at correct location?
✅ Open https://pulsetrack-frontend-henna.vercel.app/dashboard
✅ Look for SCANNER_TEST truck on map
✅ Icon should be in Mutare area (approximately)
✅ Click icon to verify coordinates
✅ Popup shows: "Coordinates: -18.9763, 32.6836"
```

---

## ⚠️ COMMON ISSUES & FIXES

| Issue | Cause | Fix |
|-------|-------|-----|
| Icon shows but at wrong location | Coordinates not saved to `FleetTruck.last_latitude` | Verify `mobile_location_update()` has `driver.truck.save()` |
| Icon doesn't appear | Coordinates are None or NaN | Check mobile is actually getting GPS signal |
| Multiple icons overlap | Different trucks at same location | Marker clustering handles this - click cluster to expand |
| Coordinates show 0,0 | Default fallback used | Check GPS permission on mobile device |
| Map rotated/zoomed wrong | Lat/lon swapped somewhere | Verify format is always `[latitude, longitude]` not `[lon, lat]` |

---

## 📊 DATA FLOW SUMMARY

```
┌─────────────────────────────────────────────────────────────────┐
│  COORDINATE FLOW: Mobile → Backend → Web                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1️⃣ MOBILE GPS                                                   │
│     Capture: expo-location every 5 sec                           │
│     Value: -18.976323, 32.683646                                 │
│                                                                  │
│  2️⃣ SEND TO BACKEND                                              │
│     POST /api/v1/mobile/location-update/                        │
│     Payload: { latitude: -18.976323, longitude: 32.683646 }    │
│                                                                  │
│  3️⃣ BACKEND SAVES                                                │
│     → FleetDriver.latitude, longitude (driver location)         │
│     → FleetTruck.last_latitude, last_longitude (map display)   │
│     → TruckLocation (audit trail)                               │
│                                                                  │
│  4️⃣ WEB FETCHES                                                  │
│     GET /api/v1/dashboard/trucks/                               │
│     Returns: latitude, longitude, current_location              │
│                                                                  │
│  5️⃣ WEB DISPLAYS                                                 │
│     GlobalMap renders marker at [-18.976323, 32.683646]        │
│     Clusters handle overlapping trucks                          │
│     Icon labeled with truck name/ID                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ SUCCESS CRITERIA

When coordinate flow is working correctly:

1. ✅ Mobile app sends location every 5 seconds
2. ✅ Backend receives and validates coordinates
3. ✅ Coordinates saved to `FleetTruck.last_latitude` and `last_longitude`
4. ✅ Web app fetches coordinates via `/api/v1/dashboard/trucks/`
5. ✅ Truck icon appears on map at correct location
6. ✅ Icon moves in real-time as mobile app moves
7. ✅ Multiple trucks at same location cluster together
8. ✅ Clicking icon shows popup with exact coordinates
9. ✅ Mission linked to truck with correct coordinates
10. ✅ No coordinate mismatches or NaN values

---

## 🔧 MONITORING & DEBUGGING

### Real-time Monitoring Script

```python
# monitor_coordinate_flow.py
import requests
from api.models_v2 import FleetTruck, TruckLocation
import time

def verify_coordinate_flow():
    """Monitor entire coordinate flow"""
    truck = FleetTruck.objects.get(truck_identifier='SCANNER_TEST')
    
    print(f"📍 SCANNER_TEST Truck Coordinates:")
    print(f"   last_latitude: {truck.last_latitude}")
    print(f"   last_longitude: {truck.last_longitude}")
    print(f"   current_location: {truck.current_location}")
    
    # Check latest location history
    latest_loc = TruckLocation.objects.filter(truck=truck).latest('timestamp')
    print(f"\n📊 Latest Location History:")
    print(f"   latitude: {latest_loc.latitude}")
    print(f"   longitude: {latest_loc.longitude}")
    print(f"   speed: {latest_loc.speed} km/h")
    print(f"   timestamp: {latest_loc.timestamp}")
    
    # Verify backend API
    response = requests.get(
        'https://pulsetrack-back.onrender.com/api/v1/dashboard/trucks/?search=SCANNER_TEST'
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('results'):
            truck_data = data['results'][0]
            print(f"\n🌐 Web API Response:")
            print(f"   latitude: {truck_data.get('latitude')}")
            print(f"   longitude: {truck_data.get('longitude')}")

# Run every 10 seconds to see real-time updates
while True:
    verify_coordinate_flow()
    print("\n" + "="*50 + "\n")
    time.sleep(10)
```

### Run the Monitor

```bash
cd c:\Users\Mugogo\Desktop\Fleet Management
python monitor_coordinate_flow.py
```

---

## 📝 NOTES

- **No mistakes allowed**: Each coordinate must flow exactly through this pipeline
- **Test with SCANNER_TEST truck**: Known test case with ID 6f91a80d-eecd-47c5-a4ac-0b546b9cb473
- **Monitor in real-time**: Run the monitoring script while testing
- **Verify at each step**: Check database, API response, then web display
