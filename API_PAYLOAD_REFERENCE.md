# Location Sync - API Payload Reference
**Date:** May 13, 2026

This document shows the exact API payloads for the three location synchronization features.

---

## 1. Mission Start - Location Sync Payload

### Endpoint
```
POST /api/v1/mobile/mission/start-tracking/
```

### Payload (NEW with location)
```json
{
    "driver_id": "550e8400-e29b-41d4-a716-446655440000",
    "mission_id": "550e8400-e29b-41d4-a716-446655440001",
    "latitude": -17.8252,
    "longitude": 31.0335
}
```

### Payload (OLD - backward compatible)
```json
{
    "driver_id": "550e8400-e29b-41d4-a716-446655440000",
    "mission_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

### Response
```json
{
    "success": true,
    "mission_id": "550e8400-e29b-41d4-a716-446655440001",
    "mission_number": "M1",
    "status": "in_progress",
    "current_location": {
        "lat": -17.8252,
        "lon": 31.0335
    },
    "origin": {
        "lat": -18.0,
        "lon": 31.5
    },
    "destination": {
        "lat": -18.5,
        "lon": 32.0
    },
    "distance_total_m": 85000,
    "progress_pct": 0,
    "tracking_id": "track_12345",
    "timestamp": "2026-05-13T14:30:00Z"
}
```

### Where It's Called
- **File:** `mobile/src/screens/QRScannerScreen.tsx`
- **Method:** `handleMissionStartTracking()`
- **Trigger:** User scans mission QR code
- **Location Source:** `locationTracker.getCurrentLocation()`

### Backend Processing
- **File:** `api/new_mission_endpoints.py`
- **Function:** `start_mission_tracking()`
- **Logic:** If latitude/longitude provided → use for mission.current_location
           Else → use mission.origin coordinates
- **Result:** Truck appears on map immediately at driver's GPS location

---

## 2. PIN Validation - Location Override Payload

### Endpoint
```
POST /api/v1/mobile/validate-pin/
```

### Payload (NEW with location)
```json
{
    "pin": "A1B2C3",
    "phone_number": "+263123456789",
    "latitude": -17.8252,
    "longitude": 31.0335
}
```

### Payload (OLD - backward compatible)
```json
{
    "pin": "A1B2C3",
    "phone_number": "+263123456789"
}
```

### Response
```json
{
    "success": true,
    "driver_id": "550e8400-e29b-41d4-a716-446655440000",
    "truck_id": "550e8400-e29b-41d4-a716-446655440002",
    "tracking_id": "track_67890",
    "token": "auth_token_abc123xyz",
    "driver_name": "John Doe",
    "truck_name": "TRUCK-001",
    "phone_number": "+263123456789",
    "gps_tracking_enabled": true,
    "location_synced": true,
    "message": "Driver linked to truck successfully"
}
```

### Where It's Called
- **File:** `mobile/src/screens/PINEntryScreen.tsx`
- **Method:** `handlePINSubmit()`
- **Trigger:** User enters PIN and clicks "Verify"
- **Location Source:** `locationTracker.getCurrentLocation()`

### Backend Processing
- **File:** `api/mobile_endpoints.py`
- **Function:** `validate_driver_pin()`
- **Logic:**
  1. Validate PIN format
  2. Find truck matching PIN hash
  3. Get or create driver by phone_number
  4. Link driver to truck
  5. **IF location provided:**
     - Update driver.latitude and driver.longitude
     - Update driver.last_location_update = now()
     - Update truck.last_latitude and truck.last_longitude
     - Update truck.last_location_ts = now()
  6. Generate tracking_id and auth token
  7. Return response with location_synced flag

### Database Changes
```sql
-- Driver table
UPDATE api_fleetdriver 
SET latitude = -17.8252, 
    longitude = 31.0335, 
    last_location_update = NOW()
WHERE id = 'driver-uuid';

-- Truck table
UPDATE api_fleettruck
SET last_latitude = -17.8252,
    last_longitude = 31.0335,
    last_location_ts = NOW()
WHERE id = 'truck-uuid';
```

---

## 3. Admin Dashboard Truck Creation - Form Payload

### Endpoint
```
POST /api/v1/trucks/  (or CREATE equivalent)
```

### Payload (NEW - all fields)
```json
{
    "truck_identifier": "TRUCK-001",
    "plate": "ABC 123",
    "make": "Toyota",
    "model": "Hiace",
    "year": 2022,
    "vin": "JTEF12346XK123456",
    "telematics_id": "TEM-001-ABC",
    "fuel_capacity_liters": 80.5,
    "maintenance_due_date": "2026-06-30",
    "status": "idle"
}
```

### Payload (OLD - minimal fields)
```json
{
    "truck_identifier": "TRUCK-001",
    "plate": "ABC 123",
    "make": "Toyota",
    "model": "Hiace",
    "status": "idle"
}
```

### Response
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "truck_identifier": "TRUCK-001",
    "plate": "ABC 123",
    "make": "Toyota",
    "model": "Hiace",
    "year": 2022,
    "vin": "JTEF12346XK123456",
    "telematics_id": "TEM-001-ABC",
    "fuel_capacity_liters": 80.5,
    "fuel_consumed_liters": 0,
    "maintenance_due_date": "2026-06-30",
    "status": "idle",
    "is_moving": false,
    "created_at": "2026-05-13T14:35:00Z",
    "updated_at": "2026-05-13T14:35:00Z"
}
```

### Where It's Called
- **File:** `client/Frontend/src/components/AdminDashboard.jsx`
- **Method:** `TrucksTable()` component
- **Trigger:** User fills form and clicks "Create Truck"
- **Location Source:** Not applicable (admin form)

### Frontend Processing
```jsx
// Form state includes all fields
const [formData, setFormData] = useState({
    truck_identifier: '',
    plate: '',
    make: '',
    model: '',
    status: 'idle',
    year: new Date().getFullYear(),
    vin: '',
    telematics_id: '',
    fuel_capacity_liters: 100,
    maintenance_due_date: '',
});

// On create, send all fields to backend
const handleCreate = async () => {
    const response = await createV1Truck(formData);
    // ... handle response
};
```

---

## 4. Location Update - Continuous Tracking Payload

### Endpoint (Separate from above - runs every 5 seconds)
```
POST /api/v1/mobile/location-update/
```

### Payload
```json
{
    "driver_id": "550e8400-e29b-41d4-a716-446655440000",
    "latitude": -17.8260,
    "longitude": 31.0340,
    "speed": 45.5,
    "accuracy": 8.5,
    "altitude": 1520.0,
    "timestamp": 1683961800000
}
```

### Response
```json
{
    "success": true,
    "driver_id": "550e8400-e29b-41d4-a716-446655440000",
    "latitude": -17.8260,
    "longitude": 31.0340,
    "saved_at": "2026-05-13T14:30:05Z"
}
```

### Where It's Called
- **File:** `mobile/src/services/locationTracker.ts`
- **Method:** `startLocationTracking()` (runs continuously)
- **Frequency:** Every 5 seconds while tracking active

### Note
This is the **existing** location update system (not modified in this session).  
It works alongside the new location sync features to provide continuous tracking.

---

## 5. Logging Examples

### Mission Start - Console Logs
```
📡 API REQUEST: POST /mobile/mission/start-tracking/
   Full URL: https://pulsetrack-back.onrender.com/api/v1/mobile/mission/start-tracking/
   Attempt: 1/3
   Body: {"driver_id":"550e8400...","mission_id":"550e8400...","latitude":-17.8252,"longitude":31.0335}

📍 Sending current location with tracking start: (-17.8252, 31.0335)

✅ SUCCESS: POST /mobile/mission/start-tracking/
✅ Mission tracking started: M1

🚀 Starting mission tracking for mission: 550e8400-e29b-41d4-a716-446655440001
```

### PIN Validation - Console Logs
```
📱 Validating PIN: A1B2C3 for phone: +263123456789

📍 Current location for PIN validation: (-17.8252, 31.0335)

✅ SUCCESS: POST /v1/mobile/validate-pin/

📱 PIN validation response: {
    "success": true,
    "driver_id": "550e8400...",
    "truck_id": "550e8400...",
    "location_synced": true
}

✅ Truck TRUCK-001 location updated on driver link: (-17.8252, 31.0335)
```

### Backend Logs - Pin Validation
```
[2026-05-13 14:30:10] INFO: PIN validation for phone_number: +263123456789
[2026-05-13 14:30:10] INFO: PIN matches truck_id: 550e8400-e29b-41d4-a716-446655440002
[2026-05-13 14:30:10] INFO: Driver created/updated: Driver name (phone: +263123456789)
[2026-05-13 14:30:10] INFO: Driver linked to truck: TRUCK-001
[2026-05-13 14:30:10] INFO: ✅ Truck TRUCK-001 location updated on driver link: (-17.8252, 31.0335)
[2026-05-13 14:30:10] INFO: Driver tracking session created: tracking_id: track_67890
```

---

## Error Handling Examples

### Mission Start - No Location Available
```json
{
    "driver_id": "550e8400-e29b-41d4-a716-446655440000",
    "mission_id": "550e8400-e29b-41d4-a716-446655440001"
}
```
**Result:** Backend uses mission origin coordinates (fallback)

### PIN Validation - Location Unavailable
```json
{
    "pin": "A1B2C3",
    "phone_number": "+263123456789"
}
```
**Result:** Driver linked without location update, workflow continues

### PIN Validation - Invalid PIN
```json
{
    "pin": "INVALID",
    "phone_number": "+263123456789",
    "latitude": -17.8252,
    "longitude": 31.0335
}
```
**Response:**
```json
{
    "error": "Invalid PIN code. Please check and try again.",
    "status": 401
}
```

---

## Summary

| Feature | Old Payload | New Payload | Change |
|---------|------------|-------------|--------|
| Mission Start | No location | Includes lat/lon | Optional addition |
| PIN Validation | No location | Includes lat/lon | Optional addition |
| Truck Creation | 5 fields | 10 fields | New fields added |
| Location Update | (unchanged) | (unchanged) | Continues as-is |

All changes are **backward compatible**. New fields/parameters are optional and don't break existing calls.

---

*API Reference prepared: May 13, 2026*
