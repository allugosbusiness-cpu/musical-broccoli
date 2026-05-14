# 🎯 COORDINATE TESTING ACTION PLAN - Mobile App Ready

## Current Status: ✅ ALL SYSTEMS READY

- ✅ Backend coordinate fixes deployed
- ✅ Dashboard API returning coordinates
- ✅ Web app marker clustering enabled
- ✅ Verification system ready

---

## 🚀 NEXT ACTION: TEST COORDINATE FLOW WITH MOBILE APP

### Step 1: Start Expo Dev Server

```bash
cd mobile
npm start
# Or press 'a' if already running
```

### Step 2: Open Mobile App in Expo Go

1. Open Expo Go app on phone
2. Scan the QR code from terminal
3. App should load (May 2026, Mutare area location shown)

### Step 3: Link to SCANNER_TEST Truck

1. On login screen, enter:
   - **Phone**: Your phone number (or any for testing)
2. Press "Get OTP" → Should get QR code
3. Scan SCANNER_TEST truck's QR code
4. Enter PIN: **1234**
5. Driver "allan mugogo" linked to truck "SCANNER_TEST"

### Step 4: Start Tracking Mission

1. App shows QR scanner
2. Scan mission QR code (or mission dropdown)
3. Press "Start Tracking"
4. **Mobile sends location immediately**: -18.976323, 32.683646

### Step 5: Monitor Coordinate Flow

**Terminal 1: Monitoring Script**
```bash
cd c:\Users\Mugogo\Desktop\Fleet Management
python verify_coordinate_flow.py
# Should show coordinates updating in Step 2
```

**Terminal 2: Watch Real-time Updates**
```bash
python monitor_coordinates.py
# Check if SCANNER_TEST truck shows correct coordinates
```

### Step 6: Verify Web Display

1. Open https://pulsetrack-frontend-henna.vercel.app/dashboard
2. **Hard refresh**: Ctrl+Shift+R (clear cache)
3. Wait for trucks to load
4. Look for **SCANNER_TEST truck icon** on map
5. **Marker clustering**:
   - If 4 trucks at same location, you'll see a cluster badge
   - Click the badge to expand and see individual trucks
6. Click SCANNER_TEST icon
7. Popup should show:
   - Coordinates: -18.9763, 32.6836
   - Status: idle or enroute
   - Speed: matches mobile speed

---

## ⚡ VERIFICATION CHECKLIST

### Mobile App Level
- [ ] App sends location every 5 seconds
- [ ] Console shows: "📍 Location: -18.976323, 32.683646"
- [ ] Speed shows actual speed (not 0)
- [ ] Accuracy shows <10 meters

### Backend Level
- [ ] POST /api/v1/mobile/location-update/ returns 200 OK
- [ ] Response shows: "success": true
- [ ] No errors in backend logs

### Database Level
- [ ] FleetTruck.last_latitude = -18.976323
- [ ] FleetTruck.last_longitude = 32.683646
- [ ] FleetTruck.current_location has timestamp
- [ ] TruckLocation audit trail records created

### Web App Level
- [ ] Dashboard API returns coordinates in ~4 seconds
- [ ] Truck icon appears on map
- [ ] Icon positioned at correct location
- [ ] Clicking icon shows correct coordinates
- [ ] Multiple truck cluster works if applicable

---

## 🐛 IF COORDINATES DON'T SHOW ON MAP

### Checklist

1. **Mobile sending coordinates?**
   ```bash
   # Check mobile console logs
   # Should see: "📍 Location update sent: lat, lon"
   ```

2. **Backend receiving?**
   ```python
   # In Django shell:
   from api.models_v2 import TruckLocation
   latest = TruckLocation.objects.filter(truck__truck_identifier='SCANNER_TEST').latest('timestamp')
   print(f"Latest: {latest.latitude}, {latest.longitude}")
   ```

3. **Truck table updated?**
   ```python
   from api.models_v2 import FleetTruck
   truck = FleetTruck.objects.get(truck_identifier='SCANNER_TEST')
   print(f"Truck coords: {truck.last_latitude}, {truck.last_longitude}")
   ```

4. **API returns coordinates?**
   ```bash
   curl -s "https://pulsetrack-back.onrender.com/api/v1/dashboard/trucks/?search=SCANNER_TEST" | python -m json.tool
   # Should show latitude and longitude in response
   ```

5. **Web app browser console?**
   ```
   Open DevTools → Console
   Look for:
   - "🔄 Transforming truck SCANNER_TEST" 
   - "✅ Transformed SCANNER_TEST: { latitude: ..., longitude: ... }"
   - "📍 Adding marker for SCANNER_TEST at ..."
   ```

---

## 📊 DATA FLOW CONFIRMATION

When you scan and start tracking, coordinates should flow through this pipeline:

```
Mobile App GPS
    ↓ (Sent every 5 sec)
Backend: POST /api/v1/mobile/location-update/
    ↓ (Backend saves to 3 tables)
FleetDriver table (driver location)
FleetTruck table (truck display location) ← WEB APP READS THIS
TruckLocation table (audit trail)
    ↓ (Web fetches every 30 sec)
Web API: GET /api/v1/dashboard/trucks/
    ↓ (Web app receives coordinates)
GlobalMap component transforms data
    ↓ (Renders truck markers)
Leaflet map displays truck icon
```

---

## ✅ SUCCESS: WHAT WORKING LOOKS LIKE

When it's working:
- ✅ You scan QR on mobile
- ✅ Within 5 seconds, mobile sends location
- ✅ Within 4-5 more seconds, web API returns updated coordinates
- ✅ Truck icon appears on map immediately
- ✅ Icon is at correct location (Mutare for test coordinates)
- ✅ Clicking icon shows exact coordinates in popup
- ✅ If other trucks at same location, cluster shows badge with count
- ✅ Expanding cluster shows all trucks
- ✅ Mission shows same coordinates as truck

---

## 📝 NOTES FOR ACCURATE COORDINATE HANDLING

1. **Latitude must be negative** (Southern hemisphere)
   - Zimbabwe: -18 to -18.99°
   
2. **Longitude must be positive** (Eastern hemisphere)
   - Zimbabwe: 25 to 35°

3. **No swapping coordinates**
   - Always: [latitude, longitude]
   - NOT: [longitude, latitude]

4. **Decimal precision**
   - Store as: 6 decimal places (-18.976323)
   - Display as: 4 decimal places (-18.9763)

5. **Clustering**
   - Trucks within ~60 pixels on screen cluster together
   - Helps with overlapping trucks at same location
   - Click cluster to expand and see individual trucks

---

## 🔧 NEXT IF ISSUES

If coordinates don't sync:
1. Check mobile console logs (Expo Go)
2. Verify driver/truck are linked
3. Confirm mission is active
4. Run `python verify_coordinate_flow.py` to diagnose
5. Check backend logs for errors
6. Verify database connection

---

## 📞 DEBUGGING COMMANDS

### Check Latest Mobile Location
```bash
sqlite3 mobile.db "SELECT latitude, longitude, speed FROM locations ORDER BY timestamp DESC LIMIT 1;"
```

### Check Backend Received
```bash
psql $DATABASE_URL -c "SELECT latitude, longitude, speed FROM api_trucklocation WHERE truck_id='6f91a80d-eecd-47c5-a4ac-0b546b9cb473' ORDER BY timestamp DESC LIMIT 1;"
```

### Check Truck Coordinates
```bash
psql $DATABASE_URL -c "SELECT last_latitude, last_longitude, current_location FROM api_fleettruck WHERE truck_identifier='SCANNER_TEST';"
```

### Check Web API
```bash
curl "https://pulsetrack-back.onrender.com/api/v1/dashboard/trucks/?search=SCANNER_TEST" | python -m json.tool | grep -A 10 "latitude\|longitude"
```

---

**Ready to test with mobile app!** 🚀
