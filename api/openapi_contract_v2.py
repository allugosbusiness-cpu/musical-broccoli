"""
Fleet Management v2.0 - REST API Contract
OpenAPI 3.0 Specification for Drivers, Trucks, Missions, Disputes

Version: 2.0.0
Date: 2026-05-05
Author: Backend Team

Key Points:
- All endpoints return 200 OK with data on success, or 4xx/5xx on error
- Authentication: Bearer token in Authorization header (not implemented in spec, assume JWT)
- RBAC: admin_only endpoints return 403 if caller is not admin
- Timestamps in ISO 8601 format
- UUIDs as string format
"""

# ==============================================================
# AUTHENTICATION & RBAC
# ==============================================================
"""
Authentication Header (all endpoints):
  Authorization: Bearer <JWT_TOKEN>

User Roles (in JWT claims):
  - fleet_admin: Can create/modify trucks, missions, drivers, resolve disputes
  - driver: Can view own profile, on_duty toggle, accept missions, file disputes
  - fleet_user: Can view (read-only) fleets, trucks, missions, drivers

RBAC Rules:
  - POST /api/v1/drivers:      admin_only
  - PATCH /api/v1/drivers/{id}: admin_only (or self + on_duty toggle)
  - POST /api/v1/trucks:        admin_only
  - PATCH /api/v1/trucks/{id}/assign: admin_only
  - POST /api/v1/missions:      admin_only
  - PATCH /api/v1/missions/{id}/status: admin_only (or driver for on_duty missions)
  - POST /api/v1/missions/{id}/disputes: driver_only
  - PATCH /api/v1/missions/{id}/disputes/{id}/resolve: admin_only
"""

# ==============================================================
# DRIVERS ENDPOINTS
# ==============================================================

"""
POST /api/v1/drivers
  Admin only: Create new driver
  
  Request:
    {
      "first_name": "John",
      "last_name": "Smith",
      "phone": "+1234567890",
      "email": "john.smith@fleet.com",
      "license_number": "DL123456",
      "license_state": "CA",
      "hire_date": "2025-01-15",
      "notes": "Recently hired from competitor"
    }
  
  Response (201):
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "John",
      "last_name": "Smith",
      "display_name": "John Smith",
      "phone": "+1234567890",
      "email": "john.smith@fleet.com",
      "license_number": "DL123456",
      "status": "active",
      "on_duty": false,
      "performance_mark": 0,
      "deliveries_count": 0,
      "created_at": "2026-05-05T10:00:00Z",
      "updated_at": "2026-05-05T10:00:00Z"
    }
  
  Error Codes:
    - 400: Missing required field, validation failed (e.g., duplicate license_number)
    - 403: Caller is not admin
    - 409: Email or license_number already exists
"""

"""
GET /api/v1/drivers
  List drivers for fleet
  
  Query Params:
    - status: "active|suspended|terminated" (optional)
    - on_duty: "true|false" (optional)
    - limit: 50 (default)
    - offset: 0 (default)
  
  Response (200):
    {
      "count": 150,
      "next": "/api/v1/drivers?offset=50&limit=50",
      "previous": null,
      "results": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "first_name": "John",
          "last_name": "Smith",
          "phone": "+1234567890",
          "status": "active",
          "on_duty": true,
          "performance_mark": 82.5,
          "deliveries_count": 25,
          "assigned_truck_id": "660e8400-e29b-41d4-a716-446655440000",
          "assigned_truck_plate": "ABC-123"
        },
        ...
      ]
    }
"""

"""
GET /api/v1/drivers/{id}
  Fetch single driver with computed fields
  
  Query Params:
    - include: "deliveries_count,performance_mark,active_missions" (optional, comma-separated)
  
  Response (200):
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "John",
      "last_name": "Smith",
      "display_name": "John Smith",
      "phone": "+1234567890",
      "email": "john.smith@fleet.com",
      "license_number": "DL123456",
      "license_state": "CA",
      "hire_date": "2025-01-15",
      "status": "active",
      "on_duty": true,
      "performance_mark": 82.5,
      "deliveries_count": 25,
      "last_active_at": "2026-05-05T09:30:00Z",
      "achievements": [
        {"key": "safety_champion", "points": 100, "awarded_at": "2026-04-01"}
      ],
      "assigned_truck": {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "plate": "ABC-123",
        "status": "enroute"
      },
      "active_missions": [
        {
          "id": "770e8400-e29b-41d4-a716-446655440000",
          "mission_number": "M-20260505-001",
          "status": "enroute",
          "progress_pct": 75.0
        }
      ],
      "created_at": "2025-01-15T08:00:00Z",
      "updated_at": "2026-05-05T09:30:00Z"
    }
  
  Error Codes:
    - 404: Driver not found
"""

"""
PATCH /api/v1/drivers/{id}
  Update driver (admin or self for on_duty toggle only)
  
  Request:
    {
      "on_duty": true,    # driver can toggle their own
      "phone": "new_number",  # admin only
      "status": "suspended",  # admin only
      "notes": "new note"  # admin only
    }
  
  Response (200): Updated driver object (same as GET /drivers/{id})
  
  Error Codes:
    - 403: Caller not admin (unless toggling own on_duty)
    - 404: Driver not found
"""

"""
POST /api/v1/drivers/{id}/on-duty-toggle
  Quick endpoint for driver to toggle on/off duty (driver or admin)
  
  Request:
    {
      "on_duty": true
    }
  
  Response (200):
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "on_duty": true,
      "updated_at": "2026-05-05T10:15:00Z"
    }
"""

# ==============================================================
# TRUCKS ENDPOINTS
# ==============================================================

"""
POST /api/v1/trucks
  Admin only: Create new truck
  
  Request:
    {
      "truck_identifier": "TRUCK-001",
      "plate": "ABC-123",
      "vin": "1G6KF5DB9G123456",
      "make": "Volvo",
      "model": "FH16",
      "year": 2024,
      "telematics_id": "TEL-12345",
      "fuel_capacity_liters": 300
    }
  
  Response (201):
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "truck_identifier": "TRUCK-001",
      "plate": "ABC-123",
      "vin": "1G6KF5DB9G123456",
      "make": "Volvo",
      "model": "FH16",
      "year": 2024,
      "status": "idle",
      "fuel_consumed_liters": 0,
      "odometer_km": 0,
      "kilometers_travelled_km": 0,
      "assigned_driver_id": null,
      "last_latitude": null,
      "last_longitude": null,
      "last_location_ts": null,
      "created_at": "2026-05-05T10:00:00Z",
      "updated_at": "2026-05-05T10:00:00Z"
    }
  
  Error Codes:
    - 400: Validation failed
    - 403: Caller not admin
    - 409: Duplicate truck_identifier, plate, vin, or telematics_id
"""

"""
GET /api/v1/trucks
  List trucks for fleet
  
  Query Params:
    - status: "idle|enroute|maintenance|decommissioned" (optional)
    - limit: 50
    - offset: 0
  
  Response (200):
    {
      "count": 45,
      "results": [
        {
          "id": "660e8400-e29b-41d4-a716-446655440000",
          "truck_identifier": "TRUCK-001",
          "plate": "ABC-123",
          "status": "enroute",
          "assigned_driver_id": "550e8400-e29b-41d4-a716-446655440000",
          "assigned_driver_name": "John Smith",
          "fuel_consumed_liters": 125.5,
          "odometer_km": 45000,
          "kilometers_travelled_km": 250,
          "last_latitude": 37.7749,
          "last_longitude": -122.4194,
          "last_location_ts": "2026-05-05T10:15:00Z"
        },
        ...
      ]
    }
"""

"""
GET /api/v1/trucks/{id}
  Fetch single truck with status
  
  Response (200):
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "truck_identifier": "TRUCK-001",
      "plate": "ABC-123",
      "vin": "1G6KF5DB9G123456",
      "make": "Volvo",
      "model": "FH16",
      "year": 2024,
      "status": "enroute",
      "fuel_capacity_liters": 300,
      "fuel_consumed_liters": 125.5,
      "fuel_consumed_pct": 41.8,
      "odometer_km": 45000,
      "kilometers_travelled_km": 250,
      "assigned_driver": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "John Smith",
        "phone": "+1234567890",
        "status": "active"
      },
      "current_missions": [
        {
          "id": "770e8400-e29b-41d4-a716-446655440000",
          "mission_number": "M-20260505-001",
          "status": "enroute",
          "progress_pct": 75.0,
          "destination_address": "123 Main St, SF, CA"
        }
      ],
      "last_location": {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "timestamp": "2026-05-05T10:15:00Z"
      },
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2026-05-05T10:15:00Z"
    }
"""

"""
PATCH /api/v1/trucks/{id}/assign
  Admin only: Assign driver to truck
  
  Request:
    {
      "driver_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  
  Response (200): Updated truck object
  
  Error Codes:
    - 400: driver_id not provided
    - 403: Caller not admin
    - 404: Truck or driver not found
"""

# ==============================================================
# MISSIONS ENDPOINTS
# ==============================================================

"""
POST /api/v1/missions
  Admin only: Create new mission
  
  Request:
    {
      "mission_number": "M-20260505-001",
      "truck_id": "660e8400-e29b-41d4-a716-446655440000",
      "driver_id": "550e8400-e29b-41d4-a716-446655440000",
      "origin": {
        "lat": 37.7749,
        "lng": -122.4194,
        "address": "100 Main St, SF, CA"
      },
      "destination": {
        "lat": 37.8044,
        "lng": -122.2712,
        "address": "200 Oak Ave, Oakland, CA"
      },
      "stops": [
        {
          "stop_order": 1,
          "address": "150 Van Ness, SF, CA",
          "lat": 37.7796,
          "lng": -122.4210
        },
        {
          "stop_order": 2,
          "address": "200 Oak Ave, Oakland, CA",
          "lat": 37.8044,
          "lng": -122.2712
        }
      ],
      "priority": "high",
      "cargo": {
        "type": "electronics",
        "weight_kg": 500,
        "description": "Computer equipment shipment"
      },
      "route_polyline": "encoded_polyline_string",
      "distance_total_m": 45000
    }
  
  Response (201):
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "mission_number": "M-20260505-001",
      "truck_id": "660e8400-e29b-41d4-a716-446655440000",
      "driver_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "planned",
      "priority": "high",
      "origin": { ... },
      "destination": { ... },
      "distance_total_m": 45000,
      "distance_remaining_m": 45000,
      "progress_pct": 0,
      "stops": [ ... ],
      "eta": "2026-05-05T13:00:00Z",
      "created_at": "2026-05-05T10:00:00Z",
      "updated_at": "2026-05-05T10:00:00Z"
    }
  
  Error Codes:
    - 400: Missing origin/destination, validation failed
    - 403: Caller not admin
    - 409: Duplicate mission_number
"""

"""
GET /api/v1/missions
  List missions (filterable)
  
  Query Params:
    - status: "planned|assigned|enroute|paused|completed|cancelled" (optional)
    - truck_id: UUID (optional)
    - driver_id: UUID (optional)
    - priority: "low|normal|high|urgent" (optional)
    - limit: 50
    - offset: 0
  
  Response (200):
    {
      "count": 200,
      "results": [
        {
          "id": "770e8400-e29b-41d4-a716-446655440000",
          "mission_number": "M-20260505-001",
          "truck_identifier": "TRUCK-001",
          "driver_name": "John Smith",
          "status": "enroute",
          "priority": "high",
          "origin_address": "100 Main St, SF, CA",
          "destination_address": "200 Oak Ave, Oakland, CA",
          "distance_total_m": 45000,
          "distance_remaining_m": 15000,
          "progress_pct": 66.7,
          "eta": "2026-05-05T13:00:00Z",
          "created_at": "2026-05-05T10:00:00Z"
        },
        ...
      ]
    }
"""

"""
GET /api/v1/missions/{id}
  Fetch single mission with full details
  
  Response (200):
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "mission_number": "M-20260505-001",
      "truck": {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "truck_identifier": "TRUCK-001",
        "plate": "ABC-123",
        "status": "enroute"
      },
      "driver": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "John Smith",
        "status": "active",
        "on_duty": true
      },
      "status": "enroute",
      "priority": "high",
      "origin": { ... },
      "destination": { ... },
      "current_location": {
        "lat": 37.7900,
        "lng": -122.4100,
        "ts": "2026-05-05T11:30:00Z"
      },
      "route_polyline": "...",
      "distance_total_m": 45000,
      "distance_remaining_m": 15000,
      "progress_pct": 66.7,
      "eta": "2026-05-05T13:00:00Z",
      "speed_kmh": 65.5,
      "cargo": { ... },
      "stops": [
        {
          "id": "880e8400-e29b-41d4-a716-446655440000",
          "stop_order": 1,
          "address": "150 Van Ness, SF, CA",
          "status": "completed",
          "arrived_at": "2026-05-05T10:30:00Z",
          "departed_at": "2026-05-05T10:35:00Z"
        },
        {
          "id": "990e8400-e29b-41d4-a716-446655440000",
          "stop_order": 2,
          "address": "200 Oak Ave, Oakland, CA",
          "status": "pending",
          "arrived_at": null,
          "departed_at": null
        }
      ],
      "disputes": [
        {
          "id": "aa0e8400-e29b-41d4-a716-446655440000",
          "dispute_type": "incorrect_location",
          "description": "Stop location is wrong",
          "status": "open",
          "created_at": "2026-05-05T11:00:00Z"
        }
      ],
      "events": [
        {
          "id": 12345,
          "event_type": "status_changed",
          "payload": {"old_status": "assigned", "new_status": "enroute"},
          "created_at": "2026-05-05T10:00:00Z"
        }
      ],
      "created_at": "2026-05-05T09:00:00Z",
      "updated_at": "2026-05-05T11:30:00Z"
    }
"""

"""
PATCH /api/v1/missions/{id}/status
  Update mission status (admin or driver for own missions)
  
  Request:
    {
      "status": "enroute"  # planned|assigned|enroute|paused|completed|cancelled
    }
  
  Response (200): Updated mission object
  
  Error Codes:
    - 400: Invalid status, cannot transition from current status
    - 403: Caller not admin and not assigned driver
    - 404: Mission not found
"""

"""
PATCH /api/v1/missions/{id}/stops/{stop_id}
  Mark stop as completed (driver or admin)
  
  Request:
    {
      "status": "completed"
    }
  
  Response (200):
    {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "stop_order": 1,
      "address": "150 Van Ness, SF, CA",
      "status": "completed",
      "arrived_at": "2026-05-05T10:30:00Z",
      "departed_at": "2026-05-05T10:35:00Z"
    }
"""

# ==============================================================
# DISPUTES ENDPOINTS
# ==============================================================

"""
POST /api/v1/missions/{id}/disputes
  Driver files dispute about mission (driver only)
  
  Request:
    {
      "dispute_type": "incorrect_location",  # incorrect_location|wrong_cargo|timeout|...
      "stop_id": "880e8400-e29b-41d4-a716-446655440000",  # optional, which stop
      "description": "The stop location on GPS doesn't match the provided address",
      "photo_url": "https://..."  # optional, evidence photo
    }
  
  Response (201):
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440000",
      "mission_id": "770e8400-e29b-41d4-a716-446655440000",
      "driver_id": "550e8400-e29b-41d4-a716-446655440000",
      "stop_id": "880e8400-e29b-41d4-a716-446655440000",
      "dispute_type": "incorrect_location",
      "description": "The stop location on GPS doesn't match the provided address",
      "photo_url": "https://...",
      "status": "open",
      "created_at": "2026-05-05T11:00:00Z",
      "resolved_at": null
    }
  
  Error Codes:
    - 403: Caller not assigned driver for this mission
    - 404: Mission not found
"""

"""
GET /api/v1/missions/{id}/disputes
  List disputes for a mission (driver or admin)
  
  Response (200):
    {
      "count": 2,
      "results": [
        {
          "id": "aa0e8400-e29b-41d4-a716-446655440000",
          "dispute_type": "incorrect_location",
          "status": "open",
          "created_at": "2026-05-05T11:00:00Z"
        }
      ]
    }
"""

"""
PATCH /api/v1/missions/{id}/disputes/{dispute_id}/resolve
  Admin resolves dispute
  
  Request:
    {
      "resolution": "Correct location was used, driver misread. Resolved."
    }
  
  Response (200):
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440000",
      "status": "resolved",
      "resolved_at": "2026-05-05T12:00:00Z"
    }
  
  Error Codes:
    - 403: Caller not admin
    - 404: Dispute or mission not found
"""

# ==============================================================
# SAMPLE CURL COMMANDS
# ==============================================================

"""
1. CREATE DRIVER (Admin only)
curl -X POST http://localhost:8000/api/v1/drivers \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@fleet.com",
    "phone": "+1234567890",
    "license_number": "DL123456",
    "hire_date": "2025-01-15"
  }'

2. CREATE TRUCK (Admin only)
curl -X POST http://localhost:8000/api/v1/trucks \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "truck_identifier": "TRUCK-001",
    "plate": "ABC-123",
    "vin": "1G6KF5DB9G123456",
    "make": "Volvo",
    "model": "FH16",
    "year": 2024,
    "telematics_id": "TEL-12345",
    "fuel_capacity_liters": 300
  }'

3. CREATE MISSION (Admin only)
curl -X POST http://localhost:8000/api/v1/missions \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mission_number": "M-20260505-001",
    "truck_id": "660e8400-e29b-41d4-a716-446655440000",
    "driver_id": "550e8400-e29b-41d4-a716-446655440000",
    "origin": {"lat": 37.7749, "lng": -122.4194, "address": "100 Main St, SF"},
    "destination": {"lat": 37.8044, "lng": -122.2712, "address": "200 Oak Ave, Oakland"},
    "priority": "high",
    "stops": [
      {"stop_order": 1, "address": "150 Van Ness, SF", "lat": 37.7796, "lng": -122.4210},
      {"stop_order": 2, "address": "200 Oak Ave, Oakland", "lat": 37.8044, "lng": -122.2712}
    ]
  }'

4. TOGGLE DRIVER ON DUTY
curl -X POST http://localhost:8000/api/v1/drivers/{id}/on-duty-toggle \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"on_duty": true}'

5. ASSIGN MISSION TO DRIVER/TRUCK (Admin)
curl -X PATCH http://localhost:8000/api/v1/missions/{id}/status \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "assigned"}'

6. UPDATE MISSION STATUS TO ENROUTE
curl -X PATCH http://localhost:8000/api/v1/missions/{id}/status \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "enroute"}'

7. MARK STOP AS COMPLETED
curl -X PATCH http://localhost:8000/api/v1/missions/{id}/stops/{stop_id} \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

8. FILE DISPUTE (Driver)
curl -X POST http://localhost:8000/api/v1/missions/{id}/disputes \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_type": "incorrect_location",
    "description": "Stop location does not match provided address",
    "photo_url": "https://..."
  }'

9. RESOLVE DISPUTE (Admin)
curl -X PATCH http://localhost:8000/api/v1/missions/{id}/disputes/{dispute_id}/resolve \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resolution": "Location was correct; misunderstanding resolved"}'
"""
