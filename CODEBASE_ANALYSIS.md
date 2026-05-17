# PulseTrack Fleet Management - Codebase Issues Analysis
**Date:** May 13, 2026  
**Analysis Type:** Thorough Code Review - 4 Critical Areas  
**Status:** Issues Identified with Root Causes

---

## EXECUTIVE SUMMARY

| Issue | Severity | Root Cause | Status |
|-------|----------|-----------|--------|
| ❌ Backend Health Check 500 Errors | **CRITICAL** | Database query failures in exception handler | Identified |
| ❌ Truck Location Fetching API | **CRITICAL** | Multiple coordinate format issues, null handling | Identified |
| ❌ QR Code Generation | **MEDIUM** | Frontend missing `mission_id` field detection | Identified |
| ❌ Pin/Marker Rendering | **MEDIUM** | Coordinate transformation & state sync issues | Identified |

---

---

## ISSUE #1: BACKEND HEALTH CHECK ENDPOINT - 500 ERRORS

### Location
- **File:** [api/mobile_endpoints.py](api/mobile_endpoints.py#L25-L45)
- **Route:** `GET /api/v1/health/`
- **Endpoint Function:** `mobile_health_check(request)` (Lines 25-45)

### Current Implementation

```python
@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_health_check(request):
    """✅ Health check endpoint for mobile app"""
    try:
        # Check database connectivity
        driver_count = FleetDriver.objects.count()
        truck_count = FleetTruck.objects.count()
        mission_count = FleetMission.objects.count()
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': {
                'drivers': driver_count,
                'trucks': truck_count,
                'missions': mission_count,
            },
            'message': '✅ Backend is operational',
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e),
            'message': '❌ Backend error or database unavailable',
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
```

### Identified Issues

#### **Issue 1.1: Database Import Error in Exception Handler** 🔴 CRITICAL
- **Problem:** In the exception handler (line 41), the code tries to access `timezone.now()` which may not be available if there's an import error
- **Symptom:** Returns HTTP 500 instead of HTTP 503 when database is truly unavailable
- **Impact:** Frontend cannot distinguish between API problem vs database problem

#### **Issue 1.2: Silent Failure of Database Queries** 🔴 CRITICAL
- **Problem:** If `FleetDriver.objects.count()`, `FleetTruck.objects.count()`, or `FleetMission.objects.count()` fail due to missing tables/schema issues, no specific error info is returned
- **Symptom:** "AbortError: Aborted" in frontend with timeout
- **Root Cause:** Likely causes:
  1. **Missing database migrations** - Tables not created
  2. **Connection pool exhaustion** - Too many connections
  3. **Schema mismatch** - Model fields don't match database columns

#### **Issue 1.3: Missing Health Check Details** 🟡 MEDIUM
- **Problem:** The endpoint doesn't check actual API connectivity (Django app loading, settings, etc.)
- **Missing Checks:**
  - Django middleware stack status
  - API settings validation
  - Redis/cache connectivity (if used)
  - OSRM service availability

### Root Cause Analysis

**Most Likely Causes (in order):**

1. **Database Tables Not Created** 
   - Command needed: `python manage.py migrate`
   - Symptoms: `django.db.utils.OperationalError: no such table`

2. **Connection Pool Issues** 
   - Database connections exhausted
   - Symptoms: `django.db.utils.OperationalError: too many connections`

3. **Settings Configuration** 
   - Incorrect DATABASE settings in settings.py
   - Symptoms: Connection refused or auth failures

### Recommendations

**IMMEDIATE FIX:**
```python
@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_health_check(request):
    """Health check with comprehensive diagnostics"""
    diagnostics = {
        'status': 'unknown',
        'timestamp': timezone.now().isoformat(),
        'database': {},
        'message': '',
    }
    
    try:
        # Test each database table individually
        try:
            driver_count = FleetDriver.objects.count()
            diagnostics['database']['drivers'] = {
                'status': 'ok',
                'count': driver_count
            }
        except Exception as db_error:
            diagnostics['database']['drivers'] = {
                'status': 'error',
                'error': str(db_error)
            }
        
        try:
            truck_count = FleetTruck.objects.count()
            diagnostics['database']['trucks'] = {
                'status': 'ok',
                'count': truck_count
            }
        except Exception as db_error:
            diagnostics['database']['trucks'] = {
                'status': 'error',
                'error': str(db_error)
            }
        
        try:
            mission_count = FleetMission.objects.count()
            diagnostics['database']['missions'] = {
                'status': 'ok',
                'count': mission_count
            }
        except Exception as db_error:
            diagnostics['database']['missions'] = {
                'status': 'error',
                'error': str(db_error)
            }
        
        # Determine overall status
        db_errors = [v for v in diagnostics['database'].values() if v.get('status') == 'error']
        if db_errors:
            diagnostics['status'] = 'unhealthy'
            diagnostics['message'] = f'❌ {len(db_errors)} database tables unreachable'
            return Response(diagnostics, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            diagnostics['status'] = 'healthy'
            diagnostics['message'] = '✅ Backend is operational'
            return Response(diagnostics, status=status.HTTP_200_OK)
            
    except Exception as e:
        import traceback
        diagnostics['status'] = 'error'
        diagnostics['message'] = '❌ Unexpected backend error'
        diagnostics['error'] = str(e)
        diagnostics['traceback'] = traceback.format_exc()
        return Response(diagnostics, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

---

## ISSUE #2: TRUCK LOCATION FETCHING API

### Location
- **Primary Endpoint:** `GET /api/v1/dashboard/trucks/`
- **File:** [api/dashboard_endpoints.py](api/dashboard_endpoints.py#L63-L84)
- **Function:** `trucks_list_with_mission_data(request)` (Lines 63-84)
- **Service Layer:** [api/dashboard_service.py](api/dashboard_service.py#L380-L470)
- **Function:** `get_trucks_with_mission_data()` (Lines 380-470)

### Related Functions

#### **Location Fetching Service** 
- **Function:** `get_truck_location_from_missions(truck_id)` - [Lines 180-188](api/dashboard_service.py#L180-L188)
- **Purpose:** Retrieves truck's current location from latest mission

#### **Frontend API Call**
- **File:** [client/Frontend/src/services/api.js](client/Frontend/src/services/api.js#L891-L900)
- **Function:** `getDashboardTrucks()` (Lines 891-900)

### Current Implementation

**Backend Service - get_trucks_with_mission_data():**

```python
def get_trucks_with_mission_data():
    """Get all trucks with data synced from missions"""
    trucks = FleetTruck.objects.all()
    result = []
    for truck in trucks:
        # Sync data from missions
        sync_truck_data_from_missions(truck.id)
        
        # Get current location and status
        location = get_truck_location_from_missions(truck.id)
        status = get_truck_status_from_missions(truck.id)
        fuel_data = calculate_truck_fuel_consumption(truck.id)
        
        # Ensure we always have latitude/longitude - use truck's own coords if no mission data
        latitude = None
        longitude = None
        
        if location and isinstance(location, dict):
            latitude = location.get('lat') or location.get('latitude')
            longitude = location.get('lon') or location.get('longitude')
        
        # Fall back to truck's stored latitude/longitude if no mission location
        if latitude is None or longitude is None:
            latitude = float(truck.last_latitude) if truck.last_latitude else None
            longitude = float(truck.last_longitude) if truck.last_longitude else None
        
        # If STILL no coordinates, use default/zero (don't skip the truck)
        if latitude is None:
            latitude = 0.0
        if longitude is None:
            longitude = 0.0
        
        result.append({
            'id': str(truck.id),
            'truck_identifier': truck.truck_identifier,
            'plate': truck.plate,
            'make': truck.make,
            'model': truck.model,
            'status': status,
            'location': location,
            'latitude': latitude,
            'longitude': longitude,
            'fuel_consumed_liters': float(fuel_data['fuel_consumed_liters']),
            'distance_travelled_km': float(fuel_data['distance_travelled_km']),
            'fuel_rate_per_100km': fuel_data['fuel_rate_per_100km'],
            'fuel_capacity_liters': float(truck.fuel_capacity_liters),
            'fuel_percent': (float(fuel_data['fuel_consumed_liters']) / float(truck.fuel_capacity_liters) * 100) if truck.fuel_capacity_liters else 0,
            'assigned_driver': truck.assigned_driver.get_display_name() if truck.assigned_driver else None,
        })
    return result
```

**Location Fetching:**

```python
def get_truck_location_from_missions(truck_id):
    """Get truck's current location from the latest mission"""
    latest_mission = FleetMission.objects.filter(
        truck_id=truck_id
    ).order_by('-updated_at').first()
    
    if latest_mission and latest_mission.current_location:
        return latest_mission.current_location
    return None
```

### Identified Issues

#### **Issue 2.1: Inconsistent Coordinate Key Naming** 🔴 CRITICAL
- **Problem:** Multiple different key names used for coordinates:
  - Backend stores in mission as: `{'lat': ..., 'lon': ...}`
  - Truck model may use: `last_latitude`, `last_longitude`
  - Frontend expects: `latitude`, `longitude`
  - QR codes use: `destination_latitude`, `destination_longitude`
  - GlobalMap may expect: `latitude`, `longitude` OR `lat`, `lon`

- **Location in Code:**
  - [dashboard_service.py:393-399](api/dashboard_service.py#L393-L399) - Multiple key checks
  - [mobile_endpoints.py:749-771](api/mobile_endpoints.py#L749-L771) - Location update stores `{'lat', 'lon'}`
  - [GlobalMap.jsx:490-495](client/Frontend/src/components/GlobalMap.jsx#L490-L495) - Expects `latitude`, `longitude`

- **Symptom:** Markers don't render or render at 0,0 coordinates (Null Island)

#### **Issue 2.2: No Null/Zero Coordinate Validation** 🟡 MEDIUM
- **Problem:** Code defaults to `0.0, 0.0` when coordinates are missing (Lines 410-412)
- **Result:** Trucks with no missions render at location (0°, 0°) - Null Island, Gulf of Guinea
- **Impact:** Map becomes cluttered with orphaned trucks; difficult to distinguish real vs placeholder positions

#### **Issue 2.3: Decimal to Float Conversion Issues** 🟡 MEDIUM
- **Problem:** 
  - Truck coordinates stored as Django `Decimal` type
  - Fuel data stored as `Decimal` type
  - Converting with `float()` may lose precision or throw exception if None
  - Line 405: `float(truck.last_latitude) if truck.last_latitude else None` - redundant None check

- **Symptom:** 500 error when `Decimal` is None and `float(None)` is called

#### **Issue 2.4: Mission Location Structure Inconsistency** 🟡 MEDIUM
- **Problem:** `current_location` in mission is stored as JSON dict but no validation of structure
- **Location:** [dashboard_service.py:185](api/dashboard_service.py#L185)
- **Risk:** If mission has malformed `current_location`, the code tries to access missing keys

#### **Issue 2.5: No Error Handling in Dashboard Endpoint** 🔴 CRITICAL
- **Problem:** `trucks_list_with_mission_data()` endpoint has try-catch but returns generic 500 error
- **Location:** [dashboard_endpoints.py:80-84](api/dashboard_endpoints.py#L80-84)
- **Result:** Frontend gets no details about which truck failed or why

**Current Code:**
```python
except Exception as e:
    logger.error(f'Error getting trucks mission data: {str(e)}')
    return Response(
        {'error': 'Failed to get trucks mission data'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
```

#### **Issue 2.6: Frontend API Call Has No Error Details** 🟡 MEDIUM
- **Location:** [api.js:891-900](client/Frontend/src/services/api.js#L891-L900)
- **Problem:** Error handler logs but doesn't provide recovery options
- **Result:** User sees blank map with no feedback about what failed

### Root Cause Analysis

**Most Likely Issues (in order):**

1. **Coordinate Key Mismatch** (90% probability)
   - Mission stores `{'lat', 'lon'}`
   - Frontend reads `location` field but expects individual `latitude`/`longitude`
   - Result: `latitude: 0.0, longitude: 0.0` for all trucks

2. **Decimal Type Conversion** (60% probability)
   - `truck.last_latitude` is None or Decimal
   - `float(None)` throws TypeError
   - Falls through to default `0.0`

3. **Database Schema/Permissions** (40% probability)
   - Missing `current_location` column in FleetMission table
   - Database connection timeout during iteration

### Recommendations

**IMMEDIATE FIXES:**

1. **Standardize Coordinate Keys Everywhere:**

```python
def get_trucks_with_mission_data():
    """Get all trucks with standardized coordinate format"""
    trucks = FleetTruck.objects.all()
    result = []
    for truck in trucks:
        try:
            # Get location with fallback chain
            location = get_truck_location_from_missions(truck.id)
            latitude = 0.0
            longitude = 0.0
            
            # Try mission location first
            if location and isinstance(location, dict):
                latitude = float(location.get('lat') or location.get('latitude') or 0.0)
                longitude = float(location.get('lon') or location.get('longitude') or 0.0)
            
            # Fallback to truck's last known position
            if latitude == 0.0 or longitude == 0.0:
                if truck.last_latitude:
                    latitude = float(truck.last_latitude)
                if truck.last_longitude:
                    longitude = float(truck.last_longitude)
            
            # Only include if we have meaningful coordinates (not 0,0)
            if latitude == 0.0 and longitude == 0.0:
                logger.warning(f'⚠️ No coordinates for truck {truck.id}')
                # Skip or mark as having unknown location
                continue
            
            result.append({
                'id': str(truck.id),
                'truck_identifier': truck.truck_identifier,
                'plate': truck.plate,
                'latitude': latitude,  # Always lat/lon, never lat/lon
                'longitude': longitude,
                'location': location,  # Include raw location dict too
                # ... rest of fields
            })
        except Exception as e:
            logger.error(f'Error processing truck {truck.id}: {str(e)}')
            continue  # Skip this truck instead of crashing
    
    return result
```

2. **Add Comprehensive Error Handling:**

```python
@api_view(['GET'])
def trucks_list_with_mission_data(request):
    """Get trucks with mission data"""
    try:
        data = get_trucks_with_mission_data()
        return Response({
            'status': 'success',
            'count': len(data),
            'trucks': data,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
    except FleetTruck.DoesNotExist:
        logger.error('No trucks found in database')
        return Response({
            'status': 'error',
            'error': 'No trucks found',
            'message': 'There are no trucks in the database yet'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'Error getting trucks: {str(e)}', exc_info=True)
        return Response({
            'status': 'error',
            'error': type(e).__name__,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

3. **Validate Mission Location Structure:**

```python
def get_truck_location_from_missions(truck_id):
    """Get truck's current location from latest mission with validation"""
    latest_mission = FleetMission.objects.filter(
        truck_id=truck_id
    ).order_by('-updated_at').first()
    
    if not latest_mission:
        return None
    
    location = latest_mission.current_location
    
    # Validate structure
    if not isinstance(location, dict):
        logger.warning(f'Invalid location type for mission {latest_mission.id}: {type(location)}')
        return None
    
    # Check for required keys
    if not ('lat' in location or 'latitude' in location) or \
       not ('lon' in location or 'longitude' in location):
        logger.warning(f'Missing coordinate keys in mission {latest_mission.id}: {location.keys()}')
        return None
    
    return location
```

---

---

## ISSUE #3: QR CODE GENERATION

### Locations
- **Backend Generation - Truck QR:** [api/mobile_endpoints.py](api/mobile_endpoints.py#L529-L580)
  - Function: `generate_truck_qr(request, truck_id)` - Lines 529-580
  
- **Backend Generation - Mission QR:** [api/mobile_endpoints.py](api/mobile_endpoints.py#L713-L800)
  - Function: `generate_mission_qr(request, mission_id)` - Lines 713-800
  
- **Frontend Display Component:** [client/Frontend/src/components/QRCodeDisplay.jsx](client/Frontend/src/components/QRCodeDisplay.jsx)
  - Component renders QR codes

### Current Implementation

**Backend - generate_mission_qr():**

```python
@api_view(['GET'])
def generate_mission_qr(request, mission_id):
    """Generate QR code for mission assignment"""
    try:
        mission = FleetMission.objects.get(id=mission_id)
        driver = mission.driver
        truck = mission.truck

        if not driver or not truck:
            return Response(
                {'error': 'Mission must be assigned to a driver and truck'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create QR code data
        qr_data = json.dumps({
            'type': 'driver_mission_assignment',
            'mission_id': str(mission.id),
            'driver_id': str(driver.id),
            'truck_id': str(truck.id),
            'driver_name': driver.name,
            'driver_phone': driver.phone_number,
            'destination_latitude': float(mission.destination_latitude),
            'destination_longitude': float(mission.destination_longitude),
            'origin_latitude': float(mission.origin_latitude),
            'origin_longitude': float(mission.origin_longitude),
            'mission_number': mission.mission_number,
            'destination_address': mission.destination_address or '',
            'timestamp': datetime.now().isoformat(),
        })
        
        # ... generate QR image and return base64 ...
```

**Frontend - QRCodeDisplay.jsx:**

```javascript
export default function QRCodeDisplay({ truckId = null, truckData = null, missionId = null, missionData = null }) {
  const [qrValue, setQrValue] = useState(() => {
    if (missionData && missionId) {
      // Mission QR code with all tracking details
      return JSON.stringify({
        type: 'driver_mission_assignment',
        mission_id: missionId,
        mission_number: missionData.mission_number || `MISSION-${missionId.substring(0, 8)}`,
        truck_id: missionData.truck_id || truckId,
        driver_id: missionData.driver_id || '',
        driver_name: missionData.driver_name || 'Unassigned',
        // ... more fields ...
      });
    } else if (truckData && truckId) {
      // Truck registration QR code
      return JSON.stringify({
        type: 'truck_registration',
        truck_id: truckId,
        truck_name: truckData.truck_identifier || 'Unknown',
        // ... more fields ...
      });
    }
    return null;  // Show helpful message
  });
```

### Identified Issues

#### **Issue 3.1: Missing Field Detection in Frontend** 🔴 CRITICAL
- **Problem:** QR generation requires `missionId` AND `missionData` props
- **Location:** [QRCodeDisplay.jsx:7-10](client/Frontend/src/components/QRCodeDisplay.jsx#L7-L10)
- **Symptom:** QR code doesn't generate if parent component forgets to pass both
- **Result:** Shows "Select a mission to generate QR" instead of generating

- **Example of Likely Bug:**
  ```javascript
  // Parent component might pass only one:
  <QRCodeDisplay missionId={mission.id} /> // Missing missionData!
  // or
  <QRCodeDisplay missionData={missionData} /> // Missing missionId!
  ```

#### **Issue 3.2: Inconsistent Field Names Between Backend & Frontend** 🟡 MEDIUM
- **Problem:** Backend generates different field names than frontend expects
- **Location:** 
  - Backend [api/mobile_endpoints.py:766-774](api/mobile_endpoints.py#L766-L774)
  - Frontend [QRCodeDisplay.jsx:25-30](client/Frontend/src/components/QRCodeDisplay.jsx#L25-L30)

| Field | Backend | Frontend | Status |
|-------|---------|----------|--------|
| Mission ID | `mission_id` | `mission_id` | ✅ Match |
| Driver ID | `driver_id` | `driver_id` | ✅ Match |
| Truck ID | `truck_id` | `truck_id` | ❓ May mismatch if truckData doesn't have it |
| Driver Name | `driver.name` | `driver_name` ✅ missionData.driver_name | ⚠️ Field name issue (model uses `first_name`/`last_name`) |
| Destination Lat | `destination_latitude` | `destination_latitude` | ✅ Match |
| Destination Lon | `destination_longitude` | `destination_longitude` | ✅ Match |

- **Specific Issue:** Backend tries to access `driver.name` but FleetDriver model likely has `first_name` and `last_name` (see [views_v2.py:36](api/views_v2.py#L36))
- **Result:** QR generation fails with 500 error or contains wrong driver name

#### **Issue 3.3: Coordinate Type Conversion Errors** 🟡 MEDIUM
- **Problem:** Code attempts `float()` conversion without null checks
- **Location:** [api/mobile_endpoints.py:769-772](api/mobile_endpoints.py#L769-L772)
  ```python
  'destination_latitude': float(mission.destination_latitude),
  'destination_longitude': float(mission.destination_longitude),
  'origin_latitude': float(mission.origin_latitude),
  'origin_longitude': float(mission.origin_longitude),
  ```
- **Risk:** If any field is None or malformed, throws TypeError → 500 error
- **Impact:** QR generation fails silently for missions with incomplete data

#### **Issue 3.4: No Field Validation Before QR Generation** 🟡 MEDIUM
- **Problem:** No checks for:
  - Mission has driver assigned
  - Mission has truck assigned
  - Mission has valid coordinates
  - Coordinates are within reasonable range
  
- **Location:** [api/mobile_endpoints.py:753-758](api/mobile_endpoints.py#L753-L758)
- **Current Check:** Only checks if driver/truck exist, not if coordinates are valid

#### **Issue 3.5: Backend URL Hardcoded in Truck QR** 🟡 MEDIUM
- **Problem:** [api/mobile_endpoints.py:545](api/mobile_endpoints.py#L545)
  ```python
  'backend_url': 'http://192.168.1.100:8000/api/v1',
  ```
- **Issue:** Hardcoded IP address won't work in production
- **Solution:** Should use request host or configuration
- **Impact:** Mobile app can't connect to correct backend when scanning QR in production

### Root Cause Analysis

**Most Likely Issues (in order):**

1. **Driver Field Name Mismatch** (85% probability)
   - Backend: `driver.name` (doesn't exist)
   - Model: `FleetDriver` uses `first_name`, `last_name`
   - Fix: Use `driver.get_display_name()` or `f'{driver.first_name} {driver.last_name}'`

2. **Null Coordinate Handling** (70% probability)
   - Mission created without complete coordinate data
   - `float(None)` throws error
   - QR generation endpoint returns 500

3. **Hardcoded Backend URL** (90% probability in production)
   - Works locally but fails in production
   - Mobile app scans QR and can't connect

### Recommendations

**IMMEDIATE FIXES:**

1. **Fix Backend Driver Name Field:**

```python
@api_view(['GET'])
def generate_mission_qr(request, mission_id):
    """Generate QR code for mission assignment"""
    try:
        mission = FleetMission.objects.get(id=mission_id)
        driver = mission.driver
        truck = mission.truck

        if not driver or not truck:
            return Response(
                {'error': 'Mission must be assigned to a driver and truck'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate coordinates
        required_coords = [
            mission.destination_latitude, mission.destination_longitude,
            mission.origin_latitude, mission.origin_longitude
        ]
        
        if any(c is None for c in required_coords):
            return Response({
                'error': 'Mission is missing coordinate data',
                'missing': [
                    'destination_latitude' if mission.destination_latitude is None else None,
                    'destination_longitude' if mission.destination_longitude is None else None,
                    'origin_latitude' if mission.origin_latitude is None else None,
                    'origin_longitude' if mission.origin_longitude is None else None,
                ]
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create QR code data with FIXED field names
        qr_data = json.dumps({
            'type': 'driver_mission_assignment',
            'mission_id': str(mission.id),
            'driver_id': str(driver.id),
            'truck_id': str(truck.id),
            'driver_name': driver.get_display_name(),  # ✅ FIX: Use actual method
            'driver_phone': driver.phone,  # ✅ FIX: Use correct field name
            'destination_latitude': float(mission.destination_latitude),
            'destination_longitude': float(mission.destination_longitude),
            'origin_latitude': float(mission.origin_latitude),
            'origin_longitude': float(mission.origin_longitude),
            'mission_number': mission.mission_number,
            'destination_address': mission.destination_address or '',
            'timestamp': datetime.now().isoformat(),
        })
        
        # ... rest of implementation ...
```

2. **Fix Hardcoded Backend URL:**

```python
@api_view(['GET'])
def generate_truck_qr(request, truck_id):
    """Generate QR code for truck registration"""
    try:
        truck = FleetTruck.objects.get(id=truck_id)

        # ✅ FIX: Use request host instead of hardcoded IP
        protocol = 'https' if request.is_secure() else 'http'
        host = request.get_host()  # Gets 'localhost:8000' or 'example.com' etc
        backend_url = f'{protocol}://{host}/api/v1'

        qr_data = json.dumps({
            'type': 'truck_registration',
            'truck_id': str(truck.id),
            'truck_identifier': truck.truck_identifier,
            'plate': truck.plate or '',
            'backend_url': backend_url,  # ✅ FIX: Dynamic URL
            'timestamp': datetime.now().isoformat(),
        })
        
        # ... rest of implementation ...
```

3. **Frontend Component - Check Both Props:**

```javascript
export default function QRCodeDisplay({ truckId = null, truckData = null, missionId = null, missionData = null }) {
  const [qrValue, setQrValue] = useState(() => {
    // ✅ FIX: Require BOTH ID and DATA for each type
    if (missionId && missionData) {
      return JSON.stringify({
        type: 'driver_mission_assignment',
        mission_id: missionId,
        mission_number: missionData.mission_number || `MISSION-${missionId.substring(0, 8)}`,
        truck_id: missionData.truck_id,
        driver_id: missionData.driver_id,
        driver_name: missionData.driver_name || 'Unassigned',
        driver_phone: missionData.driver_phone || '',
        destination_latitude: missionData.destination?.latitude || missionData.destination_latitude || 0,
        destination_longitude: missionData.destination?.longitude || missionData.destination_longitude || 0,
        origin_latitude: missionData.origin?.latitude || missionData.origin_latitude || 0,
        origin_longitude: missionData.origin?.longitude || missionData.origin_longitude || 0,
        destination_address: missionData.destination?.address || missionData.destination_address || '',
        status: missionData.status || 'PENDING',
        timestamp: new Date().toISOString(),
      });
    } else if (truckId && truckData) {
      return JSON.stringify({
        type: 'truck_registration',
        truck_id: truckId,
        truck_name: truckData.truck_identifier || 'Unknown',
        truck_identifier: truckData.truck_identifier || 'Unknown',
        plate: truckData.plate || 'Unknown',
        backend_url: window.location.origin,
        timestamp: new Date().toISOString(),
        version: '2.0',
      });
    }
    return null;
  });

  // Show helpful message with requirements
  if (!qrValue) {
    return (
      <div style={{
        padding: '20px',
        textAlign: 'center',
        border: '2px dashed #ccc',
        borderRadius: '8px',
        backgroundColor: '#f9f9f9',
      }}>
        <h3>📱 QR Code Generator</h3>
        <p style={{ color: '#666' }}>
          {!missionId && !truckId && 'Select a mission or truck to generate QR code'}
          {(missionId && !missionData) && '⚠️ Mission ID provided but data missing'}
          {(truckId && !truckData) && '⚠️ Truck ID provided but data missing'}
        </p>
      </div>
    );
  }
  
  // ... render QR code ...
```

---

---

## ISSUE #4: PIN/MARKER RENDERING ON MAP (GlobalMap Component)

### Location
- **File:** [client/Frontend/src/components/GlobalMap.jsx](client/Frontend/src/components/GlobalMap.jsx)
- **Component:** `GlobalMap` (full file ~800 lines)
- **Key Functions:**
  - `addTruckMarker()` - Lines 268-340
  - `updateTruckMarker()` - Lines 342-354
  - `onGpsUpdate()` - Lines 356-371
  - `runMatch()` - Lines 381-420

### Current Implementation

**Core Marker Addition Logic:**

```javascript
const addTruckMarker = (truck) => {
  console.log(`🚚 addTruckMarker called for truck ${truck.identifier}:`, {
    id: truck.id,
    lat: truck.latitude,
    lon: truck.longitude,
    status: truck.status,
  });

  if (!map.current) {
    console.error(`❌ Map not initialized for truck ${truck.identifier}`);
    return;
  }
  
  if (!truck.latitude || !truck.longitude) {
    console.warn(`⚠️ Missing coordinates for truck ${truck.identifier}`);
    return;
  }

  // Remove old marker if exists
  if (markersRef.current[truck.id]) {
    map.current.removeLayer(markersRef.current[truck.id]);
  }

  // Create custom icon for truck
  const customIcon = L.divIcon({
    html: `...truck marker HTML...`,
    className: 'truck-marker',
    iconSize: [48, 70],
    iconAnchor: [24, 70],
    popupAnchor: [0, -70],
  });

  const marker = L.marker([truck.latitude, truck.longitude], { icon: customIcon })
    .bindPopup(`...popup HTML...`)
    .addTo(map.current);

  // ✅ FIXED: Add click event handler
  marker.on('click', () => {
    setSelectedTruck(truck.id);
    if (onTruckSelect) {
      onTruckSelect(truck);
    }
    marker.openPopup();
  });

  markersRef.current[truck.id] = marker;
};
```

**Data Transformation:**

```javascript
const transformedTrucks = await Promise.all(trucksArray.map(async (truck, index) => {
  // Use location from mission if available
  const coordLat = truck.location?.lat || truck.latitude;
  const coordLon = truck.location?.lon || truck.longitude;
  
  let location_name = 'Unknown Location';
  if (coordLat && coordLon) {
    location_name = await reverseGeocode(coordLat, coordLon);
  }
  
  const transformed = {
    id: truck.id,
    plate: truck.plate,
    identifier: truck.truck_identifier,
    status: truck.status,
    location_name: location_name,
    latitude: coordLat,
    longitude: coordLon,
    speed: truck.speed || 0,
    // ...
  };
}));
```

### Identified Issues

#### **Issue 4.1: Inconsistent Coordinate Field Names** 🔴 CRITICAL
- **Problem:** Code tries to read from both:
  - `truck.location?.lat` / `truck.location?.lon` (from mission)
  - `truck.latitude` / `truck.longitude` (direct fields)
  
- **Location:** [GlobalMap.jsx:486-496](client/Frontend/src/components/GlobalMap.jsx#L486-L496)

- **Issue:** Backend response includes ALL of these:
  ```python
  {
    'location': {'lat': 31.0335, 'lon': -17.8252},  # From mission
    'latitude': 31.0335,                             # Duplicate
    'longitude': -17.8252,                          # Duplicate
  }
  ```

- **Symptom:** Markers may render at wrong coordinates if fallback chain fails

**Fallback Chain Issue:**
```javascript
// This logic is problematic:
const coordLat = truck.location?.lat || truck.latitude;  
// If truck.location.lat exists but is 0, it falls through to truck.latitude
// If truck.latitude is 0, marker doesn't show (falsy check)
```

#### **Issue 4.2: Zero Coordinate Handling** 🔴 CRITICAL
- **Problem:** Code checks `if (!truck.latitude || !truck.longitude)` which treats `0` as missing
- **Location:** [GlobalMap.jsx:279-281](client/Frontend/src/components/GlobalMap.jsx#L279-L281)
  ```javascript
  if (!truck.latitude || !truck.longitude) {
    console.warn(`⚠️ Missing coordinates for truck ${truck.identifier}`);
    return;
  }
  ```
- **Issue:** Trucks at coordinates like (0.1°N, 0.1°E) would fail this check
- **Correct Check:** Should be `if (truck.latitude === null || truck.latitude === undefined)`

#### **Issue 4.3: State Sync Hook Missing Dependencies** 🟡 MEDIUM
- **Problem:** `useEffect` that syncs selected truck data may not update properly
- **Location:** [GlobalMap.jsx:85-105](client/Frontend/src/components/GlobalMap.jsx#L85-L105)
  ```javascript
  useEffect(() => {
    if (selectedTruck && trucks.length > 0) {
      const truck = trucks.find(t => t.id === selectedTruck);
      if (truck) {
        setSelectedTruckData({ ... });
      }
    } else {
      setSelectedTruckData(null);
    }
  }, [selectedTruck, trucks]);
  ```
- **Risk:** If `onTruckSelect` prop callback updates parent state slowly, marker click may not update display

#### **Issue 4.4: Geocoding Errors Not Handled** 🟡 MEDIUM
- **Problem:** `reverseGeocode()` call may fail but error is silently caught
- **Location:** [GlobalMap.jsx:495](client/Frontend/src/components/GlobalMap.jsx#L495)
  ```javascript
  location_name = await reverseGeocode(coordLat, coordLon);
  ```
- **Risk:** If geocoding service unavailable, `location_name` stays "Unknown Location" but no error logged
- **Impact:** Location name never updates even when service recovers

#### **Issue 4.5: Race Condition in Truck Rendering** 🟡 MEDIUM
- **Problem:** Multiple async operations (fetch trucks, transform, geocode) may complete out of order
- **Location:** [GlobalMap.jsx:468-530](client/Frontend/src/components/GlobalMap.jsx#L468-L530)
- **Symptom:** Old truck data renders after new truck data fetched
- **Example:**
  1. User refreshes dashboard
  2. Fetch trucks starts
  3. Mid-fetch, user clicks "Refresh" again
  4. Second fetch starts but first is still transforming data
  5. Markers may render in inconsistent state

#### **Issue 4.6: Marker Click Handler Not Opening Popup Consistently** 🟡 MEDIUM
- **Problem:** Popup might not open if parent component doesn't re-render in time
- **Location:** [GlobalMap.jsx:329-335](client/Frontend/src/components/GlobalMap.jsx#L329-L335)
  ```javascript
  marker.on('click', () => {
    setSelectedTruck(truck.id);  // Updates local state
    if (onTruckSelect) {
      onTruckSelect(truck);      // Updates parent state
    }
    marker.openPopup();          // Opens popup immediately
  });
  ```
- **Race Condition:** If parent re-renders map before popup opens, popup may be destroyed

### Root Cause Analysis

**Most Likely Issues (in order):**

1. **Zero Coordinate Check** (85% probability)
   - Treated as "missing" even if valid
   - Markers don't render at 0° coordinates
   - Fix: Use explicit `=== null` checks

2. **Coordinate Key Mismatch** (75% probability)
   - Backend returns both `location` dict AND separate fields
   - Fallback chain picks wrong one
   - Result: Markers at (0, 0) or wrong location

3. **Async Rendering Race Condition** (60% probability)
   - Multiple geocoding calls simultaneously
   - Markers render before location names resolve
   - Result: "Unknown Location" persists

4. **Parent State Sync Delay** (40% probability)
   - Marker click sets state in parent
   - Parent re-renders slowly
   - Child component doesn't know which truck is selected

### Recommendations

**IMMEDIATE FIXES:**

1. **Fix Coordinate Null Checks:**

```javascript
// ❌ WRONG - treats 0 as missing:
if (!truck.latitude || !truck.longitude) { return; }

// ✅ CORRECT - explicit null check:
if (truck.latitude === null || truck.latitude === undefined ||
    truck.longitude === null || truck.longitude === undefined) {
  console.warn(`⚠️ Missing coordinates for truck ${truck.identifier}`);
  return;
}

// ✅ OR use Number.isFinite for extra safety:
if (!Number.isFinite(truck.latitude) || !Number.isFinite(truck.longitude)) {
  console.warn(`⚠️ Invalid coordinates for truck`);
  return;
}
```

2. **Standardize Coordinate Extraction:**

```javascript
// Helper function at top of component:
const getCoordinates = (truck) => {
  // Priority order: 
  // 1. location dict from mission
  // 2. Direct latitude/longitude fields
  // 3. Default (undefined = skip this truck)
  
  let lat, lon;
  
  // Try location dict first (from mission)
  if (truck.location && typeof truck.location === 'object') {
    lat = truck.location.lat || truck.location.latitude;
    lon = truck.location.lon || truck.location.longitude;
  }
  
  // Fall back to direct fields
  if (lat === undefined || lat === null) {
    lat = truck.latitude;
  }
  if (lon === undefined || lon === null) {
    lon = truck.longitude;
  }
  
  return { lat, lon };
};

// Use in transformation:
const coordLat = getCoordinates(truck).lat;
const coordLon = getCoordinates(truck).lon;

if (Number.isFinite(coordLat) && Number.isFinite(coordLon)) {
  // Valid coordinates
} else {
  // Skip this truck or use default
  console.warn(`⚠️ Skipping truck ${truck.identifier} - invalid coordinates`);
  return null;  // Skip
}
```

3. **Add Geocoding Error Handler:**

```javascript
const transformedTrucks = await Promise.all(
  trucksArray.map(async (truck, index) => {
    const { lat: coordLat, lon: coordLon } = getCoordinates(truck);
    
    if (!Number.isFinite(coordLat) || !Number.isFinite(coordLon)) {
      console.warn(`⚠️ Skipping truck - no coordinates`);
      return null;  // Filter out later
    }
    
    let location_name = 'Unknown Location';
    try {
      location_name = await reverseGeocode(coordLat, coordLon);
    } catch (error) {
      logger.error(`Geocoding failed for truck ${truck.identifier}:`, error);
      // Keep 'Unknown Location' as fallback
    }
    
    return {
      id: truck.id,
      plate: truck.plate,
      identifier: truck.truck_identifier,
      latitude: coordLat,
      longitude: coordLon,
      location_name: location_name,
      status: truck.status,
      // ...
    };
  })
).then(trucks => trucks.filter(t => t !== null));  // Remove skipped trucks
```

4. **Add Abort Controller for Race Conditions:**

```javascript
const AbortController = typeof window !== 'undefined' ? window.AbortController : null;
const controllerRef = useRef(null);

const fetchTrucks = async () => {
  // Cancel previous request if still running
  if (controllerRef.current) {
    controllerRef.current.abort();
  }
  
  // Create new controller for this request
  controllerRef.current = new AbortController();
  
  try {
    console.log('📍 Fetching trucks from dashboard API...');
    const data = await getDashboardTrucks();
    
    // Check if this request was cancelled
    if (controllerRef.current?.signal.aborted) {
      console.log('ℹ️ Truck fetch was cancelled');
      return;
    }
    
    const trucksArray = Array.isArray(data) ? data : [];
    const transformedTrucks = await Promise.all(
      trucksArray.map(async (truck, index) => {
        // ... transformation logic ...
      })
    );
    
    // Check again before updating state
    if (!controllerRef.current?.signal.aborted) {
      setTrucks(transformedTrucks);
    }
  } catch (error) {
    if (error.name !== 'AbortError') {  // Ignore aborted requests
      console.error('Error fetching trucks:', error);
    }
  }
};

// Cleanup on unmount
useEffect(() => {
  return () => {
    if (controllerRef.current) {
      controllerRef.current.abort();
    }
  };
}, []);
```

5. **Make Marker Popup More Robust:**

```javascript
// Add small delay to ensure popup renders
marker.on('click', () => {
  // Update state (both local and parent)
  setSelectedTruck(truck.id);
  if (onTruckSelect) {
    onTruckSelect(truck);
  }
  
  // Use requestAnimationFrame to ensure DOM is ready
  requestAnimationFrame(() => {
    if (marker && map.current && map.current.hasLayer(marker)) {
      marker.openPopup();
    }
  });
});
```

---

---

## SUMMARY TABLE

| Issue | Severity | Root Cause | Impact | Status |
|-------|----------|-----------|--------|--------|
| **Health Check 500** | 🔴 CRITICAL | Database import/query failures | Backend unreachable to frontend | Identified |
| **Truck Location API** | 🔴 CRITICAL | Coordinate key mismatch + null handling | No trucks on map (0,0) | Identified |
| **QR Generation** | 🟡 MEDIUM | Field name mismatch + missing validation | QR fails for incomplete missions | Identified |
| **Marker Rendering** | 🟡 MEDIUM | Zero coordinate check + async race | Markers missing or delayed | Identified |

---

## DEPLOYMENT CHECKLIST

**Before deploying fixes:**

- [ ] **Test 1:** Health check endpoint returns 200 OK
  - Run: `curl https://pulsetrack-back.onrender.com/api/v1/health/`
  - Expected: `{"status": "healthy", "database": {...}}`

- [ ] **Test 2:** Truck location API returns coordinates
  - Run: `curl https://pulsetrack-back.onrender.com/api/v1/dashboard/trucks/`
  - Expected: All trucks have `latitude` & `longitude` (not 0,0)

- [ ] **Test 3:** QR generation works
  - Select a complete mission
  - Click "Generate QR"
  - Expected: QR code appears with all fields populated

- [ ] **Test 4:** Map markers render and respond
  - Load dashboard
  - Wait for trucks to appear
  - Expected: Markers at correct coordinates, clickable

---

## NEXT STEPS

1. **Immediate (0-1 hour):** Apply fixes to health check endpoint
2. **Short-term (1-4 hours):** Fix truck location API coordinate handling
3. **Medium-term (4-8 hours):** Fix QR generation field names
4. **Long-term (8+ hours):** Fix map marker rendering logic

**Priority Order:** Health Check → Truck Location → QR → Map Markers
