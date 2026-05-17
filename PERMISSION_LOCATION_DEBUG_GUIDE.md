# Permission & Location Tracking Debug Guide

**Last Updated**: May 13, 2026  
**Status**: All fixes deployed ✅

## Quick Summary of Fixes

### Backend Fixes
- ✅ Fixed HTTP 500 errors on `/mobile/driver/{driver_id}/current-mission/` endpoint
- ✅ Added defensive null checks and data validation
- ✅ Support both `lat`/`lon` and `latitude`/`longitude` coordinate formats
- ✅ Proper error handling with meaningful responses

### Mobile App Fixes
- ✅ Request permissions on app startup (in _layout.tsx)
- ✅ Don't duplicate permission requests
- ✅ Increase location update frequency: 2 minutes → 5 seconds
- ✅ Improve GPS accuracy: `Location.Accuracy.High` → `Location.Accuracy.BestForNavigation`
- ✅ Add comprehensive debug logging with clear markers
- ✅ Better error messages and failure handling

---

## Testing Checklist

### 1. Permission Request Test

**What to Look For**: When you first launch the app, you should see a permission prompt.

**Steps**:
1. Uninstall app from device (or clear app data)
2. Launch app fresh
3. Check console logs in Expo CLI

**Expected Console Output**:
```
📱 [APP INIT] Requesting permissions on app startup...
✅ [APP INIT] Permissions result: 
  location: ✅ GRANTED
  notifications: ✅ GRANTED
  media: ✅ GRANTED
```

**If Permission is DENIED**:
```
❌ [APP INIT] CRITICAL: Location permission denied - app will not work
```

**What This Means**: 
- If you see the permission prompt and grant it → ✅ WORKING
- If you see no prompt → Check if app already has permission in iOS/Android settings
- If denied, go to Settings > [App Name] > Location and set to "Always"

---

### 2. Location Tracking Test

**What to Look For**: Once you start a mission (scan QR code), you should see location updates being sent.

**Steps**:
1. Make sure app has location permission
2. Scan a mission QR code to start tracking
3. Watch the console logs while moving around (or stay still to verify it works)
4. Check web app to see if truck position updates

**Expected Console Output**:
```
✅ Backend mission status updated to ENROUTE

🚀 Starting location tracking...
📡 Starting background location updates...
✅ Background location updates started (5m distance / 5s timeout)
📍 Starting foreground location polling every 5 seconds...

📍 Location received: 6.9271, 33.7347
📤 Sending location update: lat=6.9271, lon=33.7347, acc=10.5m, speed=0.0km/h
✅ Location sent to backend

📍 Location received: 6.9272, 33.7348
📤 Sending location update: lat=6.9272, lon=33.7348, acc=9.8m, speed=12.5km/h
✅ Location sent to backend
```

**If You See These Errors**:

```
❌ ERROR in GET /mobile/driver/{id}/current-mission/: HTTP 500:
```
→ Backend issue (should be fixed now, try restarting backend)

```
❌ ERROR: Get current mission error: [Error: HTTP 500: ]
```
→ Same issue, check backend logs

```
❌ Location permission denied
```
→ Go to phone settings and grant location permission

```
❌ Error getting current location
```
→ Location service might be disabled, check phone settings

---

### 3. Location Accuracy Test

**What to Look For**: Location should update every 5 seconds, and accuracy should improve with time.

**Steps**:
1. Start a mission and go outside (GPS works better outside)
2. Look at the console logs - you should see:
   - Accuracy improving: `acc=50.0m` → `acc=10.5m` → `acc=5.2m`
   - Location coordinates changing as you move
3. Check web app map - truck should move smoothly following your path

**Expected Behavior**:
- Location updates every ~5 seconds (not every 2 minutes)
- Accuracy within 10-20 meters after 30 seconds
- Truck position follows actual path on web map
- No 30-minute delays in location updates

**If Truck Position is Still Inaccurate**:
1. Make sure you're outside (GPS needs clear sky)
2. Walk around for 30+ seconds to get better fix
3. Check phone's built-in GPS (Google Maps) - if that's also inaccurate, it's a device issue
4. If only our app is inaccurate, try:
   - Stop and restart the app
   - Make sure background location permission is enabled
   - Check if other location apps work better

---

## Debug Log Markers Explained

### App Initialization
```
📱 [APP INIT] Requesting permissions...  → App is starting up
✅ [APP INIT] Permissions result:         → Permission check completed
🚀 [APP INIT] Navigating to...            → Router navigation happening
```

### Location Tracking
```
🚀 Starting location tracking...          → locationTracker.startTracking() called
📡 Starting background updates...         → Background service activated
📍 Starting foreground polling...         → Active location polling (5 second interval)
📍 Location received: lat, lon            → GPS fix obtained
📤 Sending location update...              → About to send to backend
✅ Location sent to backend               → Successfully sent
⚠️ Failed to send, queuing offline       → Will retry when online
```

### Errors
```
❌ [ERROR MESSAGE]                        → Something failed
⚠️ [WARNING MESSAGE]                      → Non-critical issue (will continue)
```

---

## Full Test Scenario

### Scenario: Complete Mission Tracking Flow

**Setup**:
- App fresh installed or with cleared data
- Device has location permission disabled initially
- Device has internet connection

**Actions**:
1. **App Launch** (~5 seconds)
   - App asks for permissions
   - You grant location permission
   - Logs show: `✅ Permissions result: location: ✅ GRANTED`

2. **Navigate to QR Scanner** (~2 seconds)
   - Go to "Scan Mission" or similar
   - Logs show normal navigation

3. **Scan Mission QR Code** (~10 seconds)
   - Point camera at mission QR
   - Scan to activate mission
   - Logs show:
     - `✅ Backend mission status updated to ENROUTE`
     - `🚀 Starting location tracking...`
     - Background and foreground updates starting

4. **Move Around** (~30 seconds)
   - Walk, drive, or move
   - Logs show:
     - `📍 Location received` every 5 seconds
     - `📤 Sending location update` with coordinates and accuracy
     - `✅ Location sent to backend`

5. **Check Web App** (~5 seconds)
   - Open web dashboard
   - See truck icon on map
   - Truck position updates as you move

**Success Indicators** ✅:
- Permission prompt appeared
- Location logs show updates every 5 seconds
- Web map shows truck position
- Truck moves as you move (within 5-10 second delay)
- Accuracy shows reasonable values (5-30 meters)

**Failure Indicators** ❌:
- No permission prompt
- Errors about HTTP 500
- No location updates in console
- Truck doesn't appear on map
- Truck position stays frozen

---

## Troubleshooting Matrix

| Symptom | Cause | Solution |
|---------|-------|----------|
| No permission prompt | App already granted/denied | Go to Settings → App → Permissions → Reset or Clear Data |
| Permission DENIED | User rejected | Go to Settings → App → Location → Enable |
| HTTP 500 errors | Backend issue | Check backend logs or restart backend service |
| No location updates | Tracking not started | Scan mission QR to activate tracking |
| Location updates but map empty | Web issue | Reload web dashboard |
| Inaccurate location | GPS signal weak | Move outside away from buildings |
| Location very delayed (30+ min) | Update interval too long | This was fixed - should be 5 seconds now |
| App crashes on startup | Permission error | Uninstall and reinstall app |

---

## Backend Logs to Check (if you can access)

If still having issues, check backend logs for these entries:

**Good Signs**:
```
✅ Backend mission status updated to ENROUTE
📤 Location update received: lat=6.9271, lon=33.7347
✅ Mission current_location initialized
```

**Bad Signs**:
```
❌ ERROR in GET /mobile/driver/...: HTTP 500
❌ Mission not found
❌ Invalid coordinates
```

---

## Next Steps

1. **Test Permission Request** (2 minutes)
   - Fresh install
   - Look for permission prompt
   - Check console logs

2. **Test Location Tracking** (5 minutes)
   - Scan mission QR
   - Check console for location updates
   - Verify every 5 seconds not 2 minutes

3. **Test Web Map** (3 minutes)
   - Open dashboard
   - Verify truck appears
   - Move and check it follows

4. **Test Accuracy** (10+ minutes)
   - Go outside
   - Walk around for a minute
   - Check if accuracy improves over time

**Report Back With**:
- Console logs showing the flow (from app startup to location updates)
- Screenshot of web map with truck position
- Any error messages you see

---

## Code Changes for Reference

**Backend**: `api/mobile_endpoints.py:mobile_driver_current_mission()`
- Added null checks for driver.truck
- Better error handling
- Defensive coordinate extraction

**Mobile**: `mobile/app/_layout.tsx`
- Permissions requested on app init with logging

**Mobile**: `mobile/src/services/locationTracker.ts`
- Don't duplicate permission requests
- Check existing status first
- Improved logging at each stage

**Mobile**: `mobile/src/services/rateLimitedTracking.ts`
- Uses 5 second update interval (from 2 minutes)
- Best available GPS accuracy
- Better backend communication

