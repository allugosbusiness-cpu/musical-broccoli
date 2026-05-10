# Delivery Confirmation System - Architecture & Data Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PULSETRACK FLEET SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────┐              ┌──────────────────────────────┐  │
│  │  ADMIN DASHBOARD    │              │   MOBILE APP (Driver)         │  │
│  │  (Web Browser)      │              │   (React Native)              │  │
│  │                     │              │                               │  │
│  │ • Create Mission    │◄──QR Code───►│ • Scan Mission QR            │  │
│  │ • Assign Driver     │   (with      │ • Start Tracking             │  │
│  │ • View Deliveries   │   dest.)     │ • Drive to Location          │  │
│  │ • Set Destination   │              │ • Auto-Detect Arrival        │  │
│  │                     │              │ • Show Confirmation          │  │
│  └──────────┬──────────┘              └────────────┬─────────────────┘  │
│             │                                       │                    │
│             └───────────────────┬───────────────────┘                    │
│                                 │                                        │
│                    ┌────────────▼──────────────┐                        │
│                    │   DJANGO BACKEND API      │                        │
│                    │   (Port 8000)              │                        │
│                    │                           │                        │
│      ┌─────────────┤  Endpoints:               ├─────────────┐         │
│      │             │  • /mobile/.../*          │             │         │
│      │             │  • /v1/mission/*          │             │         │
│      │             │  • /v1/driver/*           │             │         │
│      │             └────────────┬──────────────┘             │         │
│      │                          │                            │         │
│  ┌───▼──────────────────────────▼────────────────────────────▼────┐   │
│  │               SQLite / PostgreSQL DATABASE                    │   │
│  │                                                               │   │
│  │  Tables:                                                      │   │
│  │  • fleet_drivers        [on_duty, deliveries_count]        │   │
│  │  • fleet_missions       [status, delivered_at]             │   │
│  │  • fleet_trucks         [status]                            │   │
│  │  • fleet_truck_locations [timestamp, speed]                │   │
│  │  • fleet_mission_events [audit trail]                       │   │
│  │                                                               │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Mission Assignment to Delivery

```
STEP 1: Mission Creation (Admin Dashboard)
┌─────────────────────────────────────────────┐
│ Admin creates mission                        │
│ • Origin: Harare (17.8252, 31.0335)         │
│ • Destination: Mutare (-18.9833, 32.6667)   │
│ • Driver: John Doe                          │
│ • Truck: TR-001                             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Generate Mission QR Code                     │
│ {                                           │
│   "type": "driver_mission_assignment",       │
│   "mission_id": "mis-uuid-001",              │
│   "driver_id": "drv-uuid-001",               │
│   "truck_id": "trk-uuid-001",                │
│   "driver_name": "John Doe",                 │
│   "destination_latitude": -18.9833,          │
│   "destination_longitude": 32.6667           │
│ }                                           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
        QR Code displayed on screen
             (Driver scans it)


STEP 2: Mission Scanning (Mobile App)
┌─────────────────────────────────────────────┐
│ Driver Scans Mission QR                      │
│ • Opens camera                               │
│ • Focuses on QR code                         │
│ • Parses JSON data                           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Extract Destination Coordinates              │
│ destination_latitude = -18.9833              │
│ destination_longitude = 32.6667              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Create Delivery Callback Function            │
│ onDeliveryDetected() {                       │
│   POST /mobile/mission/{id}/delivery/        │
│   Show "✅ Delivery Confirmed" alert         │
│   Update driver.on_duty = false              │
│ }                                           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Initialize Rate-Limited Tracker              │
│ • Start: Continuous location tracking        │
│ • Interval: Every 5 seconds                  │
│ • Destination: Stored in memory              │
│ • Callback: Ready to trigger                 │
│ Alert: "Tracking Started"                    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
        Driver drives toward destination


STEP 3: Real-Time Tracking (Every 5 seconds)
┌─────────────────────────────────────────────┐
│ Location Tracking Loop                       │
│ • Get current GPS coordinates                │
│ • speed = 65 km/h                           │
│ • latitude = -18.5000 (current)              │
│ • longitude = 32.1000 (current)              │
│ • timestamp = now()                          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Send to Backend (Rate Limited)                │
│ POST /v1/mobile/location-update/              │
│ {                                           │
│   "driver_id": "drv-uuid-001",               │
│   "latitude": -18.5000,                      │
│   "longitude": 32.1000,                      │
│   "speed": 65,                               │
│   "timestamp": 1715254000000                 │
│ }                                           │
│ Backend updates: TruckLocation, Alert check  │
│ Backend updates: Dashboard (real-time)       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
        (Continues every 5 seconds)
        Distance to destination decreasing...
        350m → 300m → 200m → 100m → 50m


STEP 4: Delivery Detection (Distance ≤ 100m)
┌─────────────────────────────────────────────┐
│ Delivery Check Loop (Every 5 seconds)        │
│                                             │
│ Haversine Formula:                          │
│ distance = 6371000m * acos(               │
│   sin(lat1) * sin(lat2) +                 │
│   cos(lat1) * cos(lat2) * cos(lon2-lon1)  │
│ )                                          │
│                                             │
│ Result: distance = 98.5 meters             │
│ Threshold: 100 meters                      │
│ Status: distance ≤ threshold ✓ MATCH!      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 🎯 DELIVERY DETECTED!                        │
│ Driver has arrived at destination            │
│ • Invoke deliveryCallback.onDeliveryDetected │
│ • Flush any pending location data            │
│ • Stop location tracking                     │
│ • Prepare API call                           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼


STEP 5: Delivery Confirmation API Call
┌─────────────────────────────────────────────┐
│ POST /v1/mobile/mission/{mission_id}/delivery/│
│                                             │
│ Request Body:                               │
│ {                                           │
│   "driver_id": "drv-uuid-001",               │
│   "delivered_at": "2026-05-08T14:30:00Z",    │
│   "delivery_timestamp": 1715254200000        │
│ }                                           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Backend Processing                           │
│                                             │
│ 1. Fetch mission from database               │
│ 2. Verify driver_id matches                  │
│ 3. Update mission:                           │
│    • status = "completed"                    │
│    • delivered_at = timestamp                │
│    • completed_at = timestamp                │
│                                             │
│ 4. Update driver:                            │
│    • on_duty = False                         │
│    • deliveries_count += 1                   │
│    • last_active_at = now()                  │
│                                             │
│ 5. Update truck:                             │
│    • status = "idle"                         │
│                                             │
│ 6. Create audit log:                         │
│    FleetMissionEvent:                        │
│    • event_type = "status_changed"           │
│    • from_status = "in_progress"             │
│    • to_status = "completed"                 │
│    • delivery_method = "geofence_detection"  │
│                                             │
│ 7. Save all changes to database              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ API Response (200 OK)                        │
│ {                                           │
│   "success": true,                          │
│   "message": "Mission MIS-001 delivered...", │
│   "mission_id": "mis-uuid-001",              │
│   "delivered_at": "2026-05-08T14:30:00Z",    │
│   "driver_name": "John Doe",                 │
│   "driver_is_free": true,      ◄─ KEY!      │
│   "driver_deliveries_count": 5               │
│ }                                           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼


STEP 6: Mobile App Confirmation
┌─────────────────────────────────────────────┐
│ Show Alert to Driver                         │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │  ✅ Delivery Confirmed                   │ │
│ │                                          │ │
│ │  Mission delivered successfully!         │ │
│ │                                          │ │
│ │  You are now free for the next mission.  │ │
│ │                                          │ │
│ │           [ OK ]                         │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ On clicking OK:                              │
│ • Clear tracking session                     │
│ • Reset scanner                              │
│ • Navigate to dashboard                      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼


STEP 7: Driver Ready for Next Mission
┌─────────────────────────────────────────────┐
│ Dashboard Shows:                             │
│                                             │
│ Driver: John Doe                             │
│ Status: 🟢 AVAILABLE (NOT ON DUTY)         │
│ Deliveries Today: 5                         │
│ Last Delivery: 2 mins ago                   │
│ Current Mission: NONE                       │
│                                             │
│ ✓ Ready to accept next mission              │
│ ✓ Can scan next mission QR immediately      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼


STEP 8: Back to Dashboard
┌─────────────────────────────────────────────┐
│ Dashboard Updates Real-Time:                 │
│                                             │
│ Mission List:                                │
│ ┌─────────────────────────────────────────┐ │
│ │ MIS-001 (John Doe) [COMPLETED]          │ │
│ │ Destination: Mutare                      │ │
│ │ Status: ✅ Delivered                    │ │
│ │ Time: 14:30:00 (2026-05-08)             │ │
│ │ Duration: 45 minutes                     │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Truck Status:                                │
│ │ TR-001 [IDLE] ← Back to idle after       │
│ │ Driver: John Doe [AVAILABLE]             │
│ │ Ready for next mission                   │
│ └─────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

## Message Sequence Diagram

```
Driver App              Backend                 Database            Dashboard
   │                       │                        │                   │
   │ 1. Scan QR            │                        │                   │
   ├──────────────────────►│                        │                   │
   │                       │                        │                   │
   │ 2. Extract dest       │                        │                   │
   │ (Client side)         │                        │                   │
   │                       │                        │                   │
   │ 3. Start tracking     │                        │                   │
   │ (Every 5 secs)        │                        │                   │
   │                       │ 4. Location update    │                   │
   ├──────────────────────►├───────────────────────►│                   │
   │                       │                        │ 5. Update         │
   │                       │                        │ TruckLocation    │
   │                       │                        │                   │
   │ 6. Check distance     │                        │                   │
   │ (Haversine)           │                        │                   │
   │                       │                        │                   │
   │ [Distance ≤ 100m]     │                        │                   │
   │ 7. Delivery detected! │                        │                   │
   │                       │                        │                   │
   │ 8. POST /delivery/    │                        │                   │
   ├──────────────────────►│ 9. Fetch mission       │                   │
   │                       ├───────────────────────►│                   │
   │                       │                        │                   │
   │                       │ 10. Update mission     │                   │
   │                       │    (status=COMPLETED) │                   │
   │                       │ 11. Update driver      │                   │
   │                       │    (on_duty=False)    │                   │
   │                       │ 12. Create audit log   │                   │
   │                       │                        │                   │
   │                       │ 13. Save changes       │                   │
   │                       ├───────────────────────►│                   │
   │                       │                        │ 14. Broadcast     │
   │                       │                        │ WebSocket event   │
   │                       │                        ├──────────────────►│
   │ 15. 200 OK            │                        │                   │
   │◄──────────────────────┤                        │                   │
   │                       │                        │ 16. Refresh       │
   │ 16. Show alert        │                        │ mission list      │
   │ "✅ Delivered"        │                        │ (COMPLETED)       │
   │                       │                        │ Refresh driver    │
   │ 17. Navigate          │                        │ availability      │
   │ to dashboard          │                        │                   │
   │                       │                        │                   │
```

## Database State Transitions

### FleetMission Record
```
BEFORE Delivery:
┌──────────────────────────────────────┐
│ id              │ mis-uuid-001        │
│ mission_number  │ MIS-001             │
│ status          │ enroute ◄──────────┐│
│ driver_id       │ drv-uuid-001        ││
│ truck_id        │ trk-uuid-001        ││
│ delivered_at    │ NULL                ││
│ completed_at    │ NULL                ││
│ created_at      │ 14:00:00            ││
│ updated_at      │ 14:25:00 (last loc) ││
└──────────────────────────────────────┘│
        (Actively driving)               │
                                        │
        >>> Delivery detected <<<       │
                                        │
AFTER Delivery:                         │
┌──────────────────────────────────────┐│
│ id              │ mis-uuid-001        ││
│ mission_number  │ MIS-001             ││
│ status          │ completed ◄─────────┘
│ driver_id       │ drv-uuid-001        │
│ truck_id        │ trk-uuid-001        │
│ delivered_at    │ 14:30:00 ◄─ NEW!    │
│ completed_at    │ 14:30:00 ◄─ NEW!    │
│ created_at      │ 14:00:00            │
│ updated_at      │ 14:30:00 (delivery) │
└──────────────────────────────────────┘
        (Mission complete)
```

### FleetDriver Record
```
BEFORE Delivery:
┌──────────────────────────────────────┐
│ id              │ drv-uuid-001        │
│ first_name      │ John                │
│ last_name       │ Doe                 │
│ on_duty         │ true  ◄──────────┐  │
│ deliveries_count│ 4                ├──┤
│ last_active_at  │ 14:25:00         │  │
│ truck_id        │ trk-uuid-001     │  │
└──────────────────────────────────────┘│
        (Currently driving)             │
                                        │
        >>> Delivery detected <<<       │
                                        │
AFTER Delivery:                         │
┌──────────────────────────────────────┐│
│ id              │ drv-uuid-001        ││
│ first_name      │ John                ││
│ last_name       │ Doe                 ││
│ on_duty         │ false ◄─────────────┘
│ deliveries_count│ 5 ◄─ INCREMENTED!   │
│ last_active_at  │ 14:30:00 ◄─ UPDATED│
│ truck_id        │ trk-uuid-001        │
└──────────────────────────────────────┘
        (Available for next mission)
```

### FleetTruck Record
```
BEFORE Delivery:
┌──────────────────────────────────────┐
│ id              │ trk-uuid-001        │
│ plate           │ TR-001              │
│ status          │ enroute ◄────────┐  │
│ assigned_driver │ drv-uuid-001     ├──┤
│ last_location_ts│ 14:25:00         │  │
└──────────────────────────────────────┘│
        (In transit)                    │
                                        │
        >>> Delivery detected <<<       │
                                        │
AFTER Delivery:                         │
┌──────────────────────────────────────┐│
│ id              │ trk-uuid-001        ││
│ plate           │ TR-001              ││
│ status          │ idle ◄──────────────┘
│ assigned_driver │ drv-uuid-001        │
│ last_location_ts│ 14:30:00            │
└──────────────────────────────────────┘
        (Ready for next mission)
```

## Performance Characteristics

### Time Analysis
```
Step 1: QR Scan to Tracking Start
└─ Time: ~2 seconds
└─ User Action: 1 scan + 1 confirmation tap

Step 2: Continuous Tracking (5 seconds interval)
└─ Location capture: ~10ms
└─ Distance calculation: ~1ms
└─ API call: ~200ms (network dependent)
└─ Total per cycle: ~210ms

Step 3: Delivery Detection
└─ Distance check: ~1ms
└─ Status: Every 5 seconds until delivery

Step 4: Geofence Entry to Detection
└─ Entering 100m radius: 0-5 seconds (next check)
└─ Average: 2.5 seconds
└─ Maximum: 5 seconds (worst case, just missed check)

Step 5: API Confirmation to DB Update
└─ API call: ~100ms
└─ Database update: ~50ms
└─ Total: ~150ms

Step 6: Dashboard Update
└─ WebSocket push: ~50ms
└─ Frontend render: ~100ms
└─ Total: ~150ms

TOTAL TIME: From delivery to driver freedom
└─ Detection: 0-5 seconds
└─ API call + DB: ~150ms
└─ Dashboard update: ~150ms
└─ TOTAL: ~5.3 seconds (99% of the time instant)
```

### Memory Analysis
```
Mobile App:
├─ Tracking session object: ~2KB
├─ Location queue (max 50): ~5KB
├─ Callback reference: <1KB
└─ Total: ~8KB

Backend:
├─ Mission object: ~3KB
├─ Driver object: ~2KB
├─ Event object: ~1KB
└─ Total: ~6KB per delivery

Database:
├─ New record per delivery: ~500 bytes
├─ Index size: Minimal (indexed field)
└─ Scalable to millions of deliveries
```

---

**Architecture Design**: Event-driven, real-time
**Scalability**: Supports thousands of concurrent drivers
**Latency**: < 5 seconds end-to-end
**Reliability**: Automatic retry, fallback manual confirmation
**Auditability**: Full event logging for compliance
