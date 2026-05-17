# Bug Fix: Truck Icons & Routes Not Displaying on Web Map

## Issue Summary
When activating a new mission (M2) from the mobile app:
- Truck icons were NOT showing on the web map
- Location display was missing
- OSRM routes were not rendering

## Root Cause Analysis

### The Problem Flow
1. Mobile app scans mission QR code
2. Local tracking starts on mobile (GPS sending location updates)
3. **BUT** backend mission status never changes from 'PLANNED' ❌
4. `mission.current_location` stays null/empty ❌
5. Web dashboard queries truck location:
   - `get_truck_location_from_missions()` checks `mission.current_location`
   - Returns None because mission.current_location is null
6. Map gets latitude=0, longitude=0 (fallback values) ❌
7. Truck not displayed on map ❌

### Why Routes Didn't Show
- Routes need valid coordinates to render
- Without truck location, route polylines can't be drawn from origin to destination

## Solution Implemented

### File 1: `api/mobile_endpoints.py` (Already Fixed)
**Function:** `start_mission_tracking()` - Lines 875-890
**Change:** Initialize mission.current_location with origin coordinates when mission becomes ENROUTE

```python
# Start the mission
mission.status = 'enroute'
mission.driver = driver
mission.started_at = timezone.now()
# ✅ NEW: Initialize current location with origin so map can display truck immediately
if mission.origin and isinstance(mission.origin, dict):
    mission.current_location = {
        'lat': mission.origin.get('lat') or mission.origin.get('latitude'),
        'lon': mission.origin.get('lon') or mission.origin.get('longitude')
    }
mission.save()
```

### File 2: `mobile/src/screens/QRScannerScreen.tsx` (Updated)
**Function:** `handleMissionStartTracking()` - Added call to backend tracking

```typescript
// Call backend to mark mission as ENROUTE and initialize location
try {
  await apiClient.startMissionTracking(mission_id);
  console.log('✅ Backend mission status updated to ENROUTE');
} catch (error) {
  console.warn('⚠️ Could not update backend mission status, continuing local tracking...', error);
}
```

## How It Works Now

### Step-by-Step Flow
1. **Mobile App Scans Mission QR** 
   - Extracts mission_id, truck_id, destination coordinates
   
2. **Calls Backend `startMissionTracking()` Endpoint** ✅ NEW
   - Status: planned → enroute
   - Initializes current_location with origin
   - Caches tracking session
   
3. **Starts Local Location Tracking**
   - GPS service begins collecting positions
   - Sends updates to backend every 5 seconds

4. **Web Dashboard Displays Truck**
   - Fetches missions via `/api/v1/dashboard/missions/`
   - Gets mission.current_location (initially origin)
   - Renders truck icon at origin
   
5. **Truck Moves**
   - Mobile app sends location updates via `mobile_location_update()`
   - Backend updates mission.current_location
   - Map refreshes and shows truck at current position
   
6. **Routes Render**
   - Map can now display OSRM route from origin to destination
   - Routes visible because coordinates are valid

## Testing Verification

✅ Test script `test_mission_tracking_fix.py` confirms:
- Mission status changes to 'enroute'
- mission.current_location initialized with origin coordinates
- `get_truck_location_from_missions()` returns valid location
- Map will display truck at origin

```
✅ Mission status is ENROUTE
✅ Mission current_location is set: {'lat': -17.8252, 'lon': 31.0335}
✅ Coordinates valid: (-17.8252, 31.0335)
✅ Map will display truck at: (-17.8252, 31.0335)
```

## Files Modified
1. ✅ `api/mobile_endpoints.py` - Lines 875-890 (was already fixed)
2. ✅ `mobile/src/screens/QRScannerScreen.tsx` - Added backend call
3. ✅ Verified with test_mission_tracking_fix.py

## Deployment Notes
- No database migrations needed
- Changes backward compatible
- Non-fatal error handling (continues if backend call fails)
- Local tracking continues even if backend initialization fails

## Expected Result After Deployment
When activating mission M2 from mobile app:
1. ✅ Truck icon appears on web map at origin
2. ✅ OSRM route displays from origin to destination
3. ✅ As driver moves, truck location updates in real-time
4. ✅ All tracking and alerts continue to work
