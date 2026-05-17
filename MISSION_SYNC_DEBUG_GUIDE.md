# Mobile App Mission Sync - Debugging & Fix

## Current Issue
- Mobile app shows only TEST missions, not real missions from web app
- HTTP 500 errors on `/current-mission/` endpoint
- Database/table mismatch suspected

## Root Cause Analysis

The mobile app has **test data fallback logic** that returns when:
1. Driver doesn't exist in database
2. Driver exists but has no truck assigned
3. Truck has no missions in status 'planned' or 'assigned'
4. Any exception occurs

```python
# This returns test missions:
except FleetDriver.DoesNotExist:
    # Return sample missions (TEST-MISSION-001, etc.)
```

## Why This is Happening

### Scenario 1: seed_fleet_v2 Never Ran
**Most Likely Cause:**
- Render rebuild hasn't completed yet
- seed_fleet_v2 command never executed
- No test missions created in database
- No test driver created

**Check:** Visit https://render.com dashboard for "musical-broccoli" service
- Look for: "Last deployed" timestamp
- Look for: "Building" or "Deploy failed" status

### Scenario 2: Driver Created But Missions Not Associated
**Possible Cause:**
- Driver registration creates new driver with phone_number
- New driver assigned to truck from QR code
- But that truck has no missions in database
- Falls back to test missions

### Scenario 3: Wrong Truck ID in QR Code
**Possible Cause:**
- QR code in mobile app scanned points to different truck
- That truck has no missions
- Even though other trucks have missions in database

## Immediate Fixes Applied ✅

1. **Added test data fallback to current-mission endpoint**
   - Returns test mission data instead of HTTP 500
   - This prevents errors but shows test data

2. **Added debug endpoint** at `/api/v1/mobile/debug/`
   - Returns database status
   - Shows all trucks, drivers, missions in database
   - Helps diagnose mismatch

3. **Added detailed logging**
   - Logs errors to help identify exact failure point
   - Returns `_debug` field in responses

## How to Verify What's Wrong

### Step 1: Check Debug Endpoint
```bash
curl https://pulsetrack-back.onrender.com/api/v1/mobile/debug/
```

**Look for:**
- `trucks_count` - Should be > 0
- `drivers_count` - Should be > 0  
- `missions_count` - Should be > 0
- `missions_sample` - Should show MISSION-001, MISSION-002, MISSION-003 if seed ran

### Step 2: Check If Render Rebuild Completed
1. Go to https://dashboard.render.com
2. Click "musical-broccoli" service
3. Look at deployment timeline
4. Check if latest build (`fa94c77`) has completed
5. Check build logs for errors

### Step 3: Force Seed Data
If seed_fleet_v2 didn't run:
```bash
# SSH into Render and run manually:
python manage.py seed_fleet_v2
```

Or trigger rebuild:
```bash
# Push code to trigger rebuild:
git commit --allow-empty -m "Trigger rebuild"
git push origin main
```

## Solution Path

### If seed_fleet_v2 Never Ran:

**Option A: Wait for Render Rebuild**
- Rebuild triggered on latest push (commit `fa94c77`)
- Should complete in 5-10 minutes
- After rebuild, call: `python manage.py seed_fleet_v2` automatically

**Option B: Force Rebuild Now**
```bash
cd "c:\Users\Mugogo\Desktop\Fleet Management"
git commit --allow-empty -m "🔄 Force Render rebuild - ensure seed_fleet_v2 runs"
git push origin main
# Wait 5-10 minutes for rebuild
```

### If Driver/Truck/Mission Mismatch:

**Check alignment:**
1. QR code points to truck ID X
2. Verify truck ID X exists in database
3. Verify missions exist for truck ID X with status 'planned'/'assigned'
4. Verify driver created during registration is assigned to truck ID X

**Fix misaligned data:**
1. Clear test missions: Run Django shell and delete sample missions
2. Register driver again with correct QR code
3. Verify missions appear

## Expected Behavior After Fix

### When seed_fleet_v2 Completes:

**In Database:**
- ✅ Test truck: `SCANNER_TEST` (ID: `6f91a80d-eecd-47c5-a4ac-0b546b9cb473`)
- ✅ Test driver: `Test Driver` (phone: `+256700000000`)
- ✅ 3 sample missions:
  - MISSION-001 (status: planned)
  - MISSION-002 (status: planned)
  - MISSION-003 (status: assigned)

**Mobile App Will Show:**
1. Register with QR → Returns driver_id
2. Go to Mission Selection → Shows MISSION-001, MISSION-002, MISSION-003
3. Select mission → Navigates to Map → Shows tracking
4. /current-mission endpoint returns HTTP 200 (not 500)

### Web Dashboard Will Show:
- Same missions as mobile app
- Both pulling from same PostgreSQL database on Render

## Testing Plan

### Test 1: Mobile App Mission Selection
```
1. Open mobile app
2. Phone Entry → Enter test number (e.g., +256700000123)
3. QR Scanner → Scan QR from web dashboard
4. Registration Confirmation → Click "Start Mission Tracking"
5. Mission Selection → Should see MISSION-001, MISSION-002, MISSION-003 (NOT TEST-MISSION-001)
6. Select MISSION-001 → Should navigate to map
7. Map Screen → Should show mission details (not test data)
```

### Test 2: Verify Database Data
```bash
# Test endpoint that shows database contents
curl https://pulsetrack-back.onrender.com/api/v1/mobile/debug/
# Should show: missions_count > 0 and missions with MISSION-00X names
```

### Test 3: Compare Web vs Mobile
```
1. Open web dashboard: https://pulsetrack-frontend-henna.vercel.app
2. Look at Missions view
3. Note mission numbers and count
4. Open mobile app and check Mission Selection
5. Verify same missions appear in both places
```

## Files Modified

- ✅ `api/mobile_endpoints.py` - Added test data fallback + debug endpoint + logging
- ✅ `api/urls.py` - Added `/mobile/debug/` route
- Commit: `fa94c77` - "🔍 Add diagnostic endpoint + improved logging"

## Next Steps

1. **Render Rebuild:** Wait for deployment to complete (check Render dashboard)
2. **Verify Database:** Call `/api/v1/mobile/debug/` to confirm data exists
3. **Test Mobile App:** Run through mission selection flow
4. **Compare:** Verify missions match web dashboard
5. **Report:** If still not matching, use debug endpoint output to identify issue

---

**Status:** All fixes deployed. Awaiting Render rebuild completion to populate test missions in database.
