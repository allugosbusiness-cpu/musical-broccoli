# OSRM Integration Testing Guide

## Overview
The fleet management system now integrates with OSRM (Open Source Routing Machine) for accurate real-road distance calculations instead of straight-line (Haversine) approximations.

## Backend Implementation ✅
- **Endpoint**: `POST http://localhost:8000/api/v1/calculate-distance/`
- **Status**: Working and tested
- **Test Result**: Victoria Falls → Bulawayo = 465.45 km (OSRM)
- **Previous**: 355 km (Haversine) - 31% error!

### Endpoint Details
**Request format:**
```json
{
  "origin": {"lat": -17.9231, "lon": 25.8545},
  "destination": {"lat": -20.1546, "lon": 28.2839}
}
```

**Response format:**
```json
{
  "distance_meters": 465448,
  "distance_km": 465.45,
  "duration_seconds": 19801,
  "duration_minutes": 330.02
}
```

**Fallback**: If OSRM unavailable, backend uses Haversine formula automatically

## Frontend Changes ✅
- ✅ Created `calculateDistanceViOSRM()` - async function calling OSRM endpoint
- ✅ Updated `selectLocation()` - uses async distance calculation with promises
- ✅ Created `calculateProgressFromDistanceOSRM()` - async progress calculation
- ✅ Updated `handleSubmit()` - awaits OSRM results for accurate progress before saving

## Testing Procedure

### Step 1: Open Mission Form
1. Navigate to http://localhost:5174 (Fleet Management Dashboard)
2. Click on "Missions" tab if not already visible
3. Click "New Mission" button to open the form

### Step 2: Test Location Selection with Distance Calculation
1. **Select Origin Location:**
   - Click in "Origin" field
   - Type "Victoria Falls" (should autocomplete)
   - Click suggestion to select
   - Should show: Victoria Falls (-17.9231, 25.8545)

2. **Select Destination Location:**
   - Click in "Destination" field
   - Type "Bulawayo" (should autocomplete)
   - Click suggestion to select
   - Should show: Bulawayo (-20.1546, 28.2839)

3. **Verify Distance Calculation:**
   - Check console (F12 → Console tab) for OSRM API call
   - Expected log: "OSRM distance result: {distance_meters: 465448, ...}"
   - Distance field should show: **465448 meters** or **465.45 km**
   - ⚠️ DO NOT use old Haversine value of 355 km

### Step 3: Test Status-Based Progress Auto-Calculation
1. **Select Status: PLANNED**
   - Progress should auto-set to: **0%**

2. **Select Status: ASSIGNED**
   - Progress should auto-set to: **0%**

3. **Select Status: ENROUTE**
   - Select current location (e.g., "Harare")
   - Progress should calculate via OSRM distance from origin to current location
   - Check console for "OSRM distance" call for travel distance
   - Example: If traveled 100km on 465km route → ~21% progress

4. **Select Status: COMPLETED**
   - Progress should auto-set to: **100%**

### Step 4: Test Mission Submission
1. **Fill Required Fields:**
   - Mission Number: TEST-OSRM-001
   - Truck: Select a truck
   - Driver: Select a driver
   - Cargo: Test cargo
   - Origin: Victoria Falls
   - Destination: Bulawayo
   - Status: ENROUTE
   - Current Location: Some intermediate point

2. **Submit Form:**
   - Check console for "Sending mission data:" with correct progress_pct value
   - Should show green success message: "Mission created successfully"
   - ✅ Mission should save to database with OSRM-calculated distance and progress

### Step 5: Verify Database Storage
1. Open Django admin or check API response:
   ```bash
   curl http://localhost:8000/api/v1/missions/ | grep TEST-OSRM-001
   ```

2. Should show:
   - `distance_total_m`: 465448
   - `progress_pct`: calculated value based on current_location (not Haversine)
   - Status: "enroute" (lowercase)

## Expected Accuracy Improvements

### Victoria Falls → Bulawayo Route
- Haversine (OLD): 355 km straight line
- OSRM (NEW): 465 km actual road
- **Improvement**: +31% more accurate

### Victoria Falls → Hwange Route  
- Haversine (OLD): 80.6 km
- OSRM (NEW): 103 km (expected)
- **Improvement**: +28% more accurate

### Harare → Mutare Route
- Haversine (OLD): 214 km
- OSRM (NEW): 267 km (expected via main roads)
- **Improvement**: +25% more accurate

## Troubleshooting

### Issue: Distance shows as 0 or very small
- ✗ **Likely cause**: OSRM API call failed, verify both servers running
- ✓ **Check**: Open browser console → look for errors
- ✓ **Fix**: Restart Django server: `cd server && python manage.py runserver`

### Issue: Distance still shows Haversine value (355 km for Vic Falls→Bulawayo)
- ✗ **Likely cause**: Frontend cached old code
- ✓ **Fix**: Hard refresh: `Ctrl+Shift+R` (clear cache) then reload

### Issue: Form takes long time to update after selecting location
- ✓ **Expected**: OSRM API calls take 1-2 seconds over network
- ✓ **Note**: Backend OSRM fallback is automatic if public API slow

### Issue: OSRM endpoint returns 404
- ✗ **Likely cause**: Django URLs not reloaded
- ✓ **Fix**: Restart Django: `cd server && python manage.py runserver`

## Performance Notes
- OSRM public API (~1-2 second response time)
- Fallback to Haversine is automatic if OSRM unavailable
- Once response received, distance UI updates immediately
- Progress calculation uses returned distance value

## Success Criteria
✅ Distance calculation uses OSRM instead of Haversine  
✅ Victoria Falls → Bulawayo shows ~465 km (not 355 km)  
✅ Progress auto-calculates based on OSRM distance  
✅ Missions save with OSRM-calculated distances to database  
✅ ENROUTE missions show accurate progress percentages  

## Files Modified
1. `/client/Frontend/src/components/AdminDashboard.jsx` - Frontend OSRM integration (4 functions updated)
2. `/server/api/osrm_endpoints.py` - Backend OSRM endpoint (already created)
3. `/server/api/urls.py` - URL routing (already updated)

## Next Steps After Testing
- [ ] Test with multiple location pairs to verify accuracy
- [ ] Monitor OSRM API response times in production
- [ ] Set up fallback monitoring for when OSRM is unavailable
- [ ] Consider self-hosted Valhalla alternative for offline capability
