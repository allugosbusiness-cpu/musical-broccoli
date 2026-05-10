# Real-Time GPS Tracking & Auto-Display Trail System

## ✅ What's New

This update implements three major features for real-time fleet tracking:

### 1. **Real-Time GPS Position Recording** 
- **Endpoint**: `POST /api/trucks/{truck_id}/record_gps_position/`
- **Purpose**: Mobile app driver GPS tracking - submit location every few seconds
- **Auto-Features**:
  - Automatically updates truck current location in database
  - Auto-creates speed violation alerts when speed > 120 km/h
  - Records TrackPoint in GPS history

**Example Usage (Mobile App)**:
```javascript
// Every 5 seconds, driver app sends GPS location
await recordGPSPosition('TRUCK-001', latitude, longitude, speed, heading)
```

### 2. **Auto-Display Trails on GlobalMap**
- **Feature**: Truck trails now display automatically on the map
- **Refresh Rate**: Every 10 seconds
- **What You See**:
  - Gray dashed line showing truck's GPS trail history
  - Current position marker at the end of trail
  - All trucks' trails display simultaneously
  - No need to click "View Directions" button anymore

**Map Display Changes**:
- When you load the dashboard, you'll immediately see all trucks with their trails
- Trails update every 10 seconds automatically
- Each truck's current position shown as a light blue circle

### 3. **Real-Time KPI Metrics** 
- **Endpoint**: `GET /api/alerts/calculate_kpis/`
- **Metrics Tracked**:
  - Active Trucks: Count of moving trucks
  - On-Time Rate: Percentage of delivered trucks at 100% progress
  - Average Speed: Mean speed across all trucks
  - Total Deliveries: Count of delivered trucks
  - **Speed Violations**: Count of overspeeding alerts (>120 km/h)
  - **Critical Alerts**: Count of unresolved critical alerts

**KPI Update**: KPI Cards now fetch from centralized endpoint, updating every 5 seconds

---

## 🚀 Architecture

### Backend Changes

**New API Endpoints Added**:
1. `/api/trucks/{id}/record_gps_position/` - Record real-time driver position
2. `/api/trucks/all_trucks_with_trails/` - Get all trucks with their trails
3. `/api/alerts/calculate_kpis/` - Calculate real-time metrics

**Speed Violation Detection**:
```python
if speed > 120:  # km/h
    Alert.objects.create(
        truck=truck,
        alert_type='warning',
        message=f"Overspeeding detected: {speed} km/h (limit: 120 km/h)",
        driver_name=truck.driver
    )
```

### Frontend Changes

**GlobalMap.jsx**:
- New `useEffect` hook loads trails for ALL trucks every 10 seconds
- Trails display as subtle gray dashed polylines on map
- Each truck's latest GPS point marked with blue circle
- Trails persist on map unless you zoom/pan heavily

**KPICards.jsx**:
- Now calls `/api/alerts/calculate_kpis/` endpoint first
- Falls back to manual calculation if API unavailable
- Updates every 5 seconds for real-time metrics
- Speed violations now properly counted from database

**API Client (api.js)**:
- `recordGPSPosition()` - Submit GPS from mobile app
- `getAllTrucksWithTrails()` - Fetch all trucks with trails

---

## 📱 For Mobile App Integration

The system is now ready for mobile driver app development. Here's how to integrate:

### Step 1: Get Truck Authentication
```bash
POST /api/auth/login/
{
  "username": "driver_username",
  "password": "password"
}
```

### Step 2: Record GPS Every 5 Seconds
```javascript
// In mobile app background service
setInterval(async () => {
  const location = await getGPSLocation(); // Native device location
  await recordGPSPosition(
    truckId,
    location.latitude,
    location.longitude,
    location.speed,        // Optional
    location.heading,      // Optional
    location.altitude,     // Optional
    location.accuracy      // Optional
  );
}, 5000); // Every 5 seconds
```

### What Happens:
- GPS points are recorded to database
- Truck's current location updates immediately
- Speed violations auto-alert fleet manager
- Web dashboard shows live trail

---

## ✅ Testing the Features

### Test 1: Record GPS Position
```powershell
$body = @{
    latitude = -17.8252
    longitude = 31.0335
    speed = 95.5
    heading = 180
    altitude = 1500
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/trucks/TRUCK-001/record_gps_position/" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

**Response** (Status 201):
```json
{
  "id": "3f91d8bd-119c-43b1-8236-63a339756f68",
  "truck": "TRUCK-001",
  "latitude": -17.8252,
  "longitude": 31.0335,
  "speed": 95.5,
  "timestamp": "2026-04-29T09:20:51.823486Z"
}
```

### Test 2: Trigger Speed Violation
```powershell
$body = @{
    latitude = -17.925
    longitude = 31.05
    speed = 135.0  # Over 120 limit
    heading = 45
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/trucks/TRUCK-002/record_gps_position/" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

Alert automatically created in database!

### Test 3: Check KPI Metrics
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/alerts/calculate_kpis/" -Method GET
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Response**:
```json
{
  "timestamp": "2026-04-29T09:21:05.476955Z",
  "metrics": {
    "active_trucks": 4,
    "total_trucks": 5,
    "on_time_rate": 20.0,
    "avg_speed": 85.5,
    "total_deliveries": 1,
    "speed_violations": 1,
    "critical_alerts": 0
  }
}
```

### Test 4: View Dashboard
Open http://localhost:5174/ and you should see:
1. ✅ All truck markers on map with real-time status
2. ✅ Gray dashed trails showing GPS history for each truck
3. ✅ KPI cards showing:
   - Active Trucks: 4
   - Speed Violations: 1
   - Critical Alerts: 0
4. ✅ Trails update every 10 seconds automatically

---

## 🔧 Configuration

### Speed Violation Thresholds
Edit in `api/views.py`, `record_gps_position` method:
```python
SPEED_LIMIT = 120  # km/h - change this value
if speed > SPEED_LIMIT:
    Alert.objects.create(...)
```

### Trail Update Frequency
Edit in `GlobalMap.jsx`:
```javascript
const trailInterval = setInterval(loadAllTrails, 10000); // 10 seconds
```

### KPI Update Frequency  
Edit in `KPICards.jsx`:
```javascript
const interval = setInterval(calculateKPIs, 5000); // 5 seconds
```

---

## 🎯 Future Enhancements

1. **Authentication for Mobile App** - JWT tokens for driver login
2. **Background Geolocation Service** - Automatic tracking when app closed
3. **Geofencing** - Alerts when truck enters/exits zones
4. **Route Optimization** - Auto-reroute based on real-time traffic
5. **Offline Mode** - Queue GPS points when offline, sync when reconnected
6. **WebSocket Real-Time Updates** - Replace 5-10 second polling with live WebSocket

---

## 📊 Database Impact

New data points recorded:
- **TrackPoint**: 1 record per GPS position (every 5 seconds from mobile)
- **Alert**: 1 warning per speed violation (>120 km/h)
- Example: One truck → 12 TrackPoints/min = 17,280/day

Consider database cleanup/archival strategy for historical data.

---

## ✨ Summary

✅ Real-time GPS tracking endpoint ready for mobile app
✅ Auto-display trails on web dashboard  
✅ Speed violation detection working
✅ KPI metrics calculating correctly
✅ System scales to multiple concurrent GPS submissions

**Next Steps**: Deploy mobile driver app using the new `recordGPSPosition` endpoint!
