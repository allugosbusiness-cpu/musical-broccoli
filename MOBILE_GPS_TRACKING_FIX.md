# Mobile GPS Tracking - Critical Fixes Applied

## Summary of Fixes

### 1. **Fixed Missing API Methods** ✅
- **File**: `mobile/src/services/api.ts`
- **Issue**: `rateLimitedTracking.ts` was calling non-existent `saveDriverLocations()` and `sendDriverAlerts()` methods
- **Fix**: Added batch location and alert sending methods that loop through and send each item individually
- **Impact**: Mobile app can now send location updates to backend without crashing

### 2. **Fixed GPS Speed Conversion** ✅
- **File**: `mobile/src/services/locationTracker.ts`
- **Issue**: Speed was being converted multiple times (m/s → km/h multiple times), or not sent correctly
- **Fix**: Simplified to convert speed from m/s to km/h ONCE in `processLocationUpdate()` before sending
- **Impact**: Speed now accurately reflects actual movement (when GPS provides speed data)

### 3. **Removed Duplicate GPS Polling** ✅
- **Files**: `mobile/src/services/locationTracker.ts`, `mobile/src/services/rateLimitedTracking.ts`
- **Issue**: Both services were polling GPS independently, creating two parallel update streams
- **Fix**: 
  - `locationTracker` now handles ALL GPS polling (5 second intervals)
  - `locationTracker` sends locations directly to backend via `/api/v1/mobile/location-update/`
  - `rateLimitedTracking` removed location polling, only handles alerts & delivery detection
- **Impact**: Single, controlled GPS update stream; no more duplicate API calls

### 4. **Simplified Location Update Flow** ✅
- **Before**: Complex batching/queuing system
- **After**: Direct immediate sending with offline queue as backup
  1. `locationTracker` gets GPS every 5s
  2. Converts speed from m/s to km/h
  3. Sends immediately to backend
  4. Falls back to offline queue if backend unavailable
  5. Backend saves to FleetTruck display fields AND TruckLocation audit table

## Expected GPS Tracking Behavior

### When Mission Tracking Starts:
```
1. User taps "Start Tracking" on mission
2. QRScannerScreen calls rateLimitedTracker.initializeTracking()
3. rateLimitedTracker calls locationTracker.startTracking()
4. locationTracker:
   - Checks location permissions (previously requested in _layout.tsx)
   - Starts foreground polling with setInterval() every 5 seconds
   - Also enables background tracking (activates when app backgrounded)
5. Every 5 seconds:
   - GPS location is captured
   - Speed converted from m/s to km/h
   - Sent to backend via POST /api/v1/mobile/location-update/
   - Backend updates FleetTruck.last_latitude/last_longitude
   - Web app shows updated truck position on map
```

### Console Logs to Watch For:

**✅ Success Sequence:**
```
📍 GPS: lat=-18.9670, lon=32.6680, speed=0.0km/h, acc=10.5m
✅ Location sent to backend
```

**❌ Problems to Debug:**

If you see these logs, check the indicated issue:

```
❌ Location permission denied
→ User denied location permission in phone settings
→ Fix: Grant location permission to app

⏱️  REQUEST TIMEOUT - Backend not responding
→ Backend may be cold-starting (Render free tier takes 30-60 seconds)
→ Fix: Wait 60 seconds and try again

❌ Failed to send location to backend, queuing offline
→ Backend temporarily unavailable but data is queued
→ No action needed - app will retry
```

## Testing GPS Tracking

### Step 1: Verify Backend is Ready
```bash
# Check backend health
curl https://pulsetrack-back.onrender.com/api/v1/health/

# Expected response:
# {"status": "healthy", "message": "Backend operational"}
```

### Step 2: Grant Location Permissions (On Real Device)

**Android:**
1. Open app → See permission prompt
2. Tap "Allow"
3. Choose "Allow all the time" for background tracking

**iOS:**
1. Open app → See permission prompt
2. Tap "Always Allow" or "While Using App"
3. Go to Settings → Privacy → Location → PulseTrack → "Always"

### Step 3: Start Mission Tracking
1. Open app
2. Tap "Mission Selection"
3. Select a mission
4. Tap "Start Tracking"
5. Confirm GPS notification appears (red dot/notification showing tracking active)

### Step 4: Test Real Movement
1. **With app open:**
   - Walk/move 100-500 meters
   - Watch Expo Go logs or app logs
   - Should see:
     ```
     📍 GPS: lat=-18.9671, lon=32.6681, speed=3.2km/h, acc=10.5m
     ✅ Location sent to backend
     ```

2. **Check Web Dashboard:**
   - Open https://pulsetrack-frontend-henna.vercel.app/dashboard
   - Map should show truck moving in real-time
   - Last update time should change every 5 seconds

3. **Background Tracking:**
   - Press home button (app goes background)
   - Continue walking/moving
   - Tracking continues in background
   - Notification shows "🔴 Driver Tracking Active"

### Step 5: Verify Backend Receives Data

**Check with Python Script:**
```bash
python verify_coordinate_flow.py
```

**Expected Output:**
```
✅ STEP 2 - Backend API verified
Status Code: 200 OK
Truck: SCANNER_TEST (ID: 6f91a80d-eecd-47c5-a4ac-0b546b9cb473)
Latitude: -18.9671 ✅ (coordinates should match your movement)
Longitude: 32.6681 ✅
Speed: 0.0 km/h (may be 0 on first read, should increase with movement)
Status: idle
```

## Troubleshooting

### Issue: "Speed shows 0 km/h even when moving"

**Possible Causes:**
1. **First GPS read**: Speed takes time to establish. Walk 50+ meters.
2. **GPS hasn't locked**: Weak signal. Wait 30-60 seconds indoors for GPS lock.
3. **Device GPS disabled**: Check Settings → Location → ensure enabled
4. **Movement too slow**: Speed calculation needs relative movement

**Fix:**
1. Ensure location permission is "Always Allow"
2. Go outdoors or near window for better GPS signal
3. Walk at normal pace (3+ km/h) for speed to register
4. Check device Settings → Location → High Accuracy mode enabled

### Issue: "Coordinates not updating on map"

**Check In This Order:**
1. **Backend receiving?**
   - Run: `python verify_coordinate_flow.py`
   - Check if coordinates match your current location
   
2. **Permission granted?**
   - Check phone Settings → Location → PulseTrack → Always Allow
   
3. **Background tracking interfering?**
   - Try killing app completely and restarting
   - Wait 5 seconds after starting tracking before moving
   
4. **Check Expo logs:**
   - Expo Go app → Logs tab
   - Look for GPS coordinate log lines
   - If no logs, GPS is not updating

### Issue: "Expo Go shows permission error"

**Android:**
```
Settings → Apps → PulseTrack (or Expo Go) → Permissions → Location
→ Select "Allow all the time"
→ Back to app → Restart
```

**iOS:**
```
Settings → Privacy → Location Services → Enable
Settings → Privacy → Location Services → PulseTrack
→ Select "Always"
```

## GPS Update Frequency

Current Configuration:
- **Foreground** (app open): Every 5 seconds OR when moved 5+ meters
- **Background** (app backgrounded): Every 5 seconds OR when moved 5+ meters
- **Distance interval**: 5 meters (updates even if 5s hasn't passed)
- **Time interval**: 5 seconds (updates even if no movement)

This means:
- Walking slowly: May see 1-2 updates per minute
- Driving: Multiple updates per second
- Stationary: Update every 5 seconds (speed = 0)

## Backend Integration

### Location Update Endpoint
**Endpoint**: `POST /api/v1/mobile/location-update/`

**Request Payload:**
```json
{
  "driver_id": "driver-uuid",
  "latitude": -18.9671,
  "longitude": 32.6681,
  "speed": 3.5,  // km/h
  "accuracy": 10.5,  // meters
  "altitude": 1200,  // meters
  "timestamp": 1715938204000  // milliseconds
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Location updated",
  "driver_id": "driver-uuid",
  "truck_id": "truck-uuid"
}
```

**Database Impact:**
- Updates `FleetDriver.latitude`, `FleetDriver.longitude`, `FleetDriver.current_speed`
- Updates `FleetTruck.last_latitude`, `FleetTruck.last_longitude` (for web display)
- Creates `TruckLocation` audit record
- Triggers overspeeding alert if speed > 120 km/h

## Testing Checklist

- [ ] Location permission granted to app
- [ ] Backend health check passes (https://pulsetrack-back.onrender.com/api/v1/health/)
- [ ] Mission tracking starts without errors
- [ ] GPS logs show location captures every 5 seconds
- [ ] Speed increases when moving (not stuck at 0)
- [ ] Web dashboard shows truck position updating
- [ ] Moved 500+ meters and position reflects movement
- [ ] Coordinates are within Zimbabwe bounds
- [ ] Background tracking notification appears
- [ ] `verify_coordinate_flow.py` shows updated coordinates

## Next Steps if Issues Persist

1. **Check Expo Logs**:
   - Open Expo Go app
   - Go to "Logs" tab
   - Search for "GPS" or "Location"
   - Look for error messages

2. **Check Network Connectivity**:
   - Run: `ping pulsetrack-back.onrender.com`
   - Should see responses (not timeouts)
   
3. **Check Backend Logs**:
   - Visit Render dashboard
   - Check deployment logs for errors
   
4. **Test on Different Network**:
   - Try WiFi vs cellular
   - Some networks may block GPS

## Code Changes Summary

### api.ts
```typescript
// ✅ NEW: Batch location sending
async saveDriverLocations(driverId, missionId, truckId, locations) {
  // Sends each location individually with proper error handling
}

// ✅ NEW: Batch alert sending  
async sendDriverAlerts(driverId, missionId, alerts) {
  // Sends each alert individually
}
```

### locationTracker.ts
```typescript
// ✅ SIMPLIFIED: Single location poll every 5 seconds
setInterval(async () => {
  const location = await Location.getCurrentPositionAsync();
  await processLocationUpdate(location);  // Sends immediately
}, 5000);

// ✅ FIXED: Speed conversion happens once
const speedKmH = (location.coords.speed || 0) * 3.6;  // m/s → km/h
await apiClient.submitLocationUpdate({ ...location, speed: speedKmH });
```

### rateLimitedTracking.ts
```typescript
// ✅ REMOVED: Duplicate GPS polling
// locationTracker handles all GPS capture now

// ✅ KEPT: Alert checking and delivery detection
setInterval(() => checkAndSendAlerts(), 10000);
setInterval(() => checkDeliveryProximity(), 5000);
```

---

**Status**: 🟢 All critical GPS tracking fixes applied and ready for testing
**Last Updated**: [Your Session]
**Next Action**: Test with real device and confirm coordinates flow to web dashboard
