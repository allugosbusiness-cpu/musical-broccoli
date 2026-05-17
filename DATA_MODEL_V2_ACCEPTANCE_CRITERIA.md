# Data Model v2.0 - Acceptance Criteria & Test Data
## Comprehensive Validation & Sample Dataset

**Date**: May 2026  
**Version**: 2.0.0  
**Purpose**: Define "done" for schema migration and provide realistic test data

---

## Acceptance Criteria

### AC1: Admin Can Create Truck (Admin Only)

**Given** an authenticated admin user  
**When** they POST /api/v1/trucks with valid truck data  
**Then** the truck is created in the new schema with status='idle'  
**And** a log entry is created in admin_audit_logs  
**And** HTTP 201 is returned with truck object

**Test Data**:
```bash
curl -X POST http://localhost:8000/api/v1/trucks \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "truck_identifier": "TRUCK-EXT-001",
    "plate": "TAB-1001",
    "vin": "1G6AE5CK4E1234567",
    "make": "Volvo",
    "model": "FH16",
    "year": 2024,
    "telematics_id": "TEL-VOLVO-001",
    "fuel_capacity_liters": 350
  }'

# Expected Response (201)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "truck_identifier": "TRUCK-EXT-001",
  "plate": "TAB-1001",
  "status": "idle",
  "fuel_capacity_liters": 350,
  "fuel_consumed_liters": 0,
  "created_at": "2026-05-05T10:00:00Z"
}
```

**Verification**:
```sql
SELECT COUNT(*) FROM admin_audit_logs 
WHERE resource_type='Truck' AND action='CREATE'
AND created_at > NOW() - INTERVAL '1 minute';
-- Expected: 1
```

### AC2: Non-Admin Cannot Create Truck (RBAC)

**Given** an authenticated non-admin user (e.g., driver, fleet_user)  
**When** they attempt POST /api/v1/trucks  
**Then** HTTP 403 Forbidden is returned  
**And** error message: "Only admins can create trucks"

**Test Data**:
```bash
curl -X POST http://localhost:8000/api/v1/trucks \
  -H "Authorization: Bearer DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"truck_identifier": "TRUCK-HACK", ...}'

# Expected Response (403)
{
  "detail": "Only admins can create trucks"
}
```

### AC3: Driver Sees Assigned Missions

**Given** a driver with assigned missions  
**When** they GET /api/v1/missions?driver_id={id}  
**Then** they see all their missions with computed fields (progress_pct, eta, distance_remaining_m)  
**And** mission count matches missions where driver_id matches  
**And** computed fields are present and valid (0-100 range)

**Test Data**:
```bash
curl -X GET "http://localhost:8000/api/v1/missions?driver_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer DRIVER_TOKEN"

# Expected Response (200)
{
  "count": 3,
  "results": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440001",
      "mission_number": "M-20260505-001",
      "status": "enroute",
      "progress_pct": 66.7,
      "distance_remaining_m": 15000,
      "eta": "2026-05-05T14:00:00Z",
      "truck": {"plate": "ABC-123"},
      "origin_address": "100 Main St, SF",
      "destination_address": "200 Oak Ave, Oakland"
    },
    ...
  ]
}
```

**Verification**:
```sql
-- Verify mission count and computed fields
SELECT COUNT(*) as mission_count, 
       COUNT(*) FILTER (WHERE progress_pct BETWEEN 0 AND 100) as valid_progress,
       COUNT(*) FILTER (WHERE distance_remaining_m >= 0) as valid_distance
FROM missions 
WHERE driver_id='550e8400-e29b-41d4-a716-446655440000'
  AND status IN ('enroute', 'paused', 'assigned');
-- Expected: 3, 3, 3 (all rows have valid computed fields)
```

### AC4: Computed Fields Update Correctly & Promptly

**Given** a mission in 'enroute' status  
**When** a stop is marked as completed  
**Then** progress_pct increases by ~50% (if 2 stops total)  
**And** distance_remaining_m decreases  
**And** updated_at timestamp reflects the update  
**And** latency is <500ms

**Test Scenario**:
1. Create mission with 2 stops
2. Mark stop 1 as completed
3. Verify mission.progress_pct ≈ 50%
4. Mark stop 2 as completed
5. Verify mission.progress_pct = 100% and status = 'completed'

**SQL Validation**:
```sql
-- Mission created at 10:00:00
INSERT INTO missions (id, mission_number, status, progress_pct, distance_remaining_m)
VALUES ('m-test-001', 'M-TEST-001', 'enroute', 0, 50000);

INSERT INTO mission_stops (mission_id, stop_order, status) VALUES ('m-test-001', 1, 'pending');
INSERT INTO mission_stops (mission_id, stop_order, status) VALUES ('m-test-001', 2, 'pending');

-- At 10:00:30, mark stop 1 complete
UPDATE mission_stops SET status='completed' WHERE mission_id='m-test-001' AND stop_order=1;
UPDATE missions SET progress_pct=50, distance_remaining_m=25000 WHERE id='m-test-001';

-- Query mission at 10:00:31 (within 1 sec)
SELECT progress_pct, distance_remaining_m, updated_at FROM missions WHERE id='m-test-001';
-- Expected: 50, 25000, 2026-05-05 10:00:30 (within 1 sec of update)

-- At 10:01:00, mark stop 2 complete
UPDATE mission_stops SET status='completed' WHERE mission_id='m-test-001' AND stop_order=2;
UPDATE missions SET progress_pct=100, distance_remaining_m=0, status='completed' WHERE id='m-test-001';

-- Query mission at 10:01:01
SELECT progress_pct, status FROM missions WHERE id='m-test-001';
-- Expected: 100, completed
```

### AC5: No Data Loss During Migration

**Given** the existing production schema (old_trucks, old_drivers, old_checkpoints)  
**When** migration backfill script runs  
**Then** all data is copied to new schema with no loss  
**And** row counts match (with expected deduplication for drivers)  
**And** sample records can be verified for accuracy

**Validation Queries**:
```sql
-- Pre-migration counts
SELECT 
  'old_trucks' as table_name, COUNT(*) as count FROM old_trucks
UNION ALL
SELECT 'old_checkpoints', COUNT(*) FROM old_checkpoints
UNION ALL
SELECT 'old_driver_records', COUNT(*) FROM old_driver_records;

-- Post-migration counts (should be approximately equal)
SELECT 
  'trucks' as table_name, COUNT(*) as count FROM trucks
UNION ALL
SELECT 'mission_stops', COUNT(*) FROM mission_stops
UNION ALL
SELECT 'drivers', COUNT(*) FROM drivers;

-- Verify no NULL foreign keys (except where allowed)
SELECT COUNT(*) as broken_fks FROM missions WHERE truck_id IS NULL OR driver_id IS NULL;
-- Expected: 0 (or count of missions without assignment, which is OK in 'planned' status)

-- Sample data integrity: random truck from old should have equivalent in new
SELECT t.truck_identifier, t.plate, t.fuel_capacity_liters
FROM trucks t
WHERE t.truck_identifier LIKE '%TRUCK%'
LIMIT 5;
-- Verify these match old schema manually

-- Check mission history preserved
SELECT COUNT(*) as completed_missions FROM missions WHERE status='completed';
-- Should be >0 if old data had completed trips
```

### AC6: Admin Audit Logs Capture All Changes

**Given** an admin performs CRUD operations (create truck, assign driver, create mission)  
**When** each operation completes  
**Then** admin_audit_logs has one row per operation  
**And** old_values and new_values are populated correctly  
**And** admin_id and resource_id match the operation

**Test Data**:
```bash
# Admin creates truck
curl -X POST http://localhost:8000/api/v1/trucks \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"truck_identifier": "TRUCK-AUDIT-001", ...}'

# Query audit log
SELECT * FROM admin_audit_logs 
WHERE action='CREATE' AND resource_type='Truck' AND created_at > NOW() - INTERVAL '1 minute';

-- Expected:
-- | id | admin_id | action | resource_type | resource_id | old_values | new_values | created_at |
-- | 1  | admin-1  | CREATE | Truck         | truck-001   | NULL       | {...}      | 2026-... |
```

### AC7: Schema Migration Completes <5 Minutes

**Given** production DB with 5+ years of data (100k+ records)  
**When** migration scripts run (0009, 0010, backfill)  
**Then** total elapsed time is <5 minutes  
**And** all tables created successfully  
**And** all indexes created successfully

**Monitoring**:
```bash
# Track migration time
START=$(date +%s)
psql < 0009_create_drivers_trucks_missions_schema_v2.sql
psql < 0010_computed_fields_views.sql
./backfill_data_v2.sh --apply
END=$(date +%s)
ELAPSED=$((END - START))

echo "Migration completed in $ELAPSED seconds"
# Expected: <300 seconds (5 min)

# Verify all tables exist
psql -c "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema='public';"
# Expected: ≥8 (drivers, trucks, missions, mission_stops, mission_events, mission_disputes, driver_performance_daily, admin_audit_logs)

# Verify indexes created
psql -c "SELECT COUNT(*) as index_count FROM pg_indexes WHERE schemaname='public';"
# Expected: ≥25
```

### AC8: API Responses <200ms p95, Backward Compatible

**Given** the new schema is live  
**When** clients call API endpoints  
**Then** p95 latency is <200ms for GET endpoints  
**And** p95 latency is <500ms for POST/PATCH endpoints  
**And** all responses follow same JSON structure as before (backward compat)  
**And** no existing API clients break

**Load Test**:
```bash
# Use Apache Bench or k6
ab -n 1000 -c 10 http://localhost:8000/api/v1/drivers/

# Expected output:
# ...
# Time per request (mean):     85 ms
# Percentage served within a certain time (ms):
#   50%    72
#   66%    91
#   75%   105
#   90%   145
#   95%   189  <-- should be <200ms
#   99%   250
```

### AC9: Dual-Write Phase Achieves 99.99% Parity

**Given** dual-write is enabled for 48 hours  
**When** both old and new schemas receive writes simultaneously  
**Then** counts match within 99.99% (e.g., 4999 out of 5000 records match)  
**And** sample records can be verified field-by-field  
**And** transformation logic is correct (enum mapping, timestamp handling, etc.)

**Validation**:
```sql
-- Run every 30 min during dual-write phase
SELECT
  'missions' as entity,
  (SELECT COUNT(*) FROM old_truck_trips WHERE created_at > NOW() - INTERVAL '1 hour') as old_count,
  (SELECT COUNT(*) FROM missions WHERE created_at > NOW() - INTERVAL '1 hour') as new_count,
  CASE 
    WHEN old_count = 0 THEN 100
    ELSE ROUND((LEAST(old_count, new_count)::numeric / GREATEST(old_count, new_count) * 100)::numeric, 2)
  END as parity_pct;

-- Expected: parity_pct >= 99.99

-- Spot-check sample records
SELECT 
  o.trip_id as old_id,
  o.truck_id as old_truck,
  o.status as old_status,
  n.id as new_id,
  n.truck_id as new_truck,
  n.status as new_status
FROM old_truck_trips o
LEFT JOIN missions n ON o.trip_id::text = n.id::text
LIMIT 10;

-- All rows should have matches
```

### AC10: Rollback Completes <30 Minutes, No Data Loss

**Given** an issue is detected (parity <99.99%, exceptions spike, latency >2s p95)  
**When** rollback is triggered  
**Then** old schema remains intact and unchanged  
**And** new schema is cleared (or kept for debugging)  
**And** all reads/writes revert to old schema  
**And** Time to recovery is <30 minutes  
**And** Zero records are lost

**Rollback Test Procedure**:
```bash
# 1. Count records in old schema before rollback
OLD_MISSION_COUNT=$(psql -c "SELECT COUNT(*) FROM old_truck_trips;" | tail -1)
echo "Old missions before: $OLD_MISSION_COUNT"

# 2. Trigger rollback
redis-cli set fleet_manager:feature_flags:new_schema_write false

# 3. Wait 5 seconds, count again
sleep 5
OLD_MISSION_COUNT_AFTER=$(psql -c "SELECT COUNT(*) FROM old_truck_trips;" | tail -1)
echo "Old missions after: $OLD_MISSION_COUNT_AFTER"

# 4. Verify counts match
if [ "$OLD_MISSION_COUNT" == "$OLD_MISSION_COUNT_AFTER" ]; then
  echo "✓ PASS: Old schema preserved, no data loss"
else
  echo "✗ FAIL: Data loss detected"
  exit 1
fi

# 5. Verify API defaults to old schema
curl http://localhost:8000/api/v1/missions | jq '.results[0]'
# Should show old schema response format
```

---

## Test Data

### Sample Drivers (5 records)

```sql
INSERT INTO drivers (
  id, fleet_id, first_name, last_name, email, phone, license_number,
  status, on_duty, performance_mark, deliveries_count, created_at
) VALUES
-- Active, on duty, high performer
('550e8400-e29b-41d4-a716-446655440001', 'fleet-001'::UUID, 'John', 'Smith', 
 'john.smith@drivers.com', '+1-555-0001', 'DL123456', 'active', true, 92.5, 45, NOW()),

-- Active, off duty, medium performer
('550e8400-e29b-41d4-a716-446655440002', 'fleet-001'::UUID, 'Jane', 'Doe',
 'jane.doe@drivers.com', '+1-555-0002', 'DL123457', 'active', false, 75.0, 28, NOW()),

-- Suspended
('550e8400-e29b-41d4-a716-446655440003', 'fleet-001'::UUID, 'Bob', 'Wilson',
 'bob.wilson@drivers.com', '+1-555-0003', 'DL123458', 'suspended', false, 45.0, 10, NOW()),

-- Active, new driver
('550e8400-e29b-41d4-a716-446655440004', 'fleet-001'::UUID, 'Alice', 'Johnson',
 'alice.johnson@drivers.com', '+1-555-0004', 'DL123459', 'active', true, 0.0, 0, NOW() - INTERVAL '7 days'),

-- On leave
('550e8400-e29b-41d4-a716-446655440005', 'fleet-001'::UUID, 'Charlie', 'Brown',
 'charlie.brown@drivers.com', '+1-555-0005', 'DL123460', 'on_leave', false, 88.0, 35, NOW() - INTERVAL '30 days');
```

### Sample Trucks (10 records)

```sql
INSERT INTO trucks (
  id, fleet_id, truck_identifier, plate, vin, make, model, year,
  telematics_id, fuel_capacity_liters, fuel_consumed_liters, odometer_km,
  status, assigned_driver_id, created_at
) VALUES
-- Idle, no driver
('660e8400-e29b-41d4-a716-446655440001', 'fleet-001'::UUID, 'TRUCK-001', 'ABC-1001', 
 '1G6AE5CK4E1234567', 'Volvo', 'FH16', 2024, 'TEL-001', 350, 0, 0, 
 'idle', NULL, NOW()),

-- En route with driver
('660e8400-e29b-41d4-a716-446655440002', 'fleet-001'::UUID, 'TRUCK-002', 'ABC-1002',
 '1G6AE5CK4E1234568', 'Volvo', 'FH16', 2023, 'TEL-002', 350, 125.5, 45000,
 'enroute', '550e8400-e29b-41d4-a716-446655440001'::UUID, NOW()),

-- Maintenance
('660e8400-e29b-41d4-a716-446655440003', 'fleet-001'::UUID, 'TRUCK-003', 'ABC-1003',
 '1G6AE5CK4E1234569', 'Scania', 'R400', 2022, 'TEL-003', 300, 200.0, 120000,
 'maintenance', NULL, NOW() - INTERVAL '10 days'),

-- Decommissioned
('660e8400-e29b-41d4-a716-446655440004', 'fleet-001'::UUID, 'TRUCK-004', 'ABC-1004',
 '1G6AE5CK4E1234570', 'MAN', 'TGX', 2020, 'TEL-004', 280, 5000.0, 500000,
 'decommissioned', NULL, NOW() - INTERVAL '90 days'),

-- Newly added idle truck (assigned to Jane)
('660e8400-e29b-41d4-a716-446655440005', 'fleet-001'::UUID, 'TRUCK-005', 'ABC-1005',
 '1G6AE5CK4E1234571', 'Volvo', 'FH16', 2024, 'TEL-005', 350, 0, 0,
 'idle', '550e8400-e29b-41d4-a716-446655440002'::UUID, NOW() - INTERVAL '1 day'),

-- High mileage truck
('660e8400-e29b-41d4-a716-446655440006', 'fleet-001'::UUID, 'TRUCK-006', 'ABC-1006',
 '1G6AE5CK4E1234572', 'DAF', 'XF', 2019, 'TEL-006', 320, 8000.0, 800000,
 'idle', NULL, NOW() - INTERVAL '365 days'),

-- 7-10: similar variations
...
```

### Sample Missions (20 records - various statuses)

```sql
INSERT INTO missions (
  id, fleet_id, mission_number, truck_id, driver_id, status, priority,
  origin, destination, distance_total_m, progress_pct, created_at, started_at
) VALUES
-- Planned, no assignment
('770e8400-e29b-41d4-a716-446655440001', 'fleet-001'::UUID, 'M-20260505-001', NULL, NULL,
 'planned', 'high', 
 '{"lat": 37.7749, "lng": -122.4194, "address": "100 Main St, SF, CA"}'::JSONB,
 '{"lat": 37.8044, "lng": -122.2712, "address": "200 Oak Ave, Oakland, CA"}'::JSONB,
 45000, 0, NOW(), NULL),

-- Assigned, not started
('770e8400-e29b-41d4-a716-446655440002', 'fleet-001'::UUID, 'M-20260505-002',
 '660e8400-e29b-41d4-a716-446655440002'::UUID,
 '550e8400-e29b-41d4-a716-446655440001'::UUID,
 'assigned', 'normal',
 '{"lat": 37.7700, "lng": -122.4100, "address": "50 Van Ness, SF"}'::JSONB,
 '{"lat": 37.9000, "lng": -122.2500, "address": "500 Market St, Oakland"}'::JSONB,
 60000, 0, NOW() - INTERVAL '2 hours', NULL),

-- En route, 2 of 3 stops complete (66% progress)
('770e8400-e29b-41d4-a716-446655440003', 'fleet-001'::UUID, 'M-20260505-003',
 '660e8400-e29b-41d4-a716-446655440002'::UUID,
 '550e8400-e29b-41d4-a716-446655440001'::UUID,
 'enroute', 'urgent',
 '{"lat": 37.7749, "lng": -122.4194, "address": "Start"}'::JSONB,
 '{"lat": 37.8500, "lng": -122.2000, "address": "End"}'::JSONB,
 80000, 66.7, NOW() - INTERVAL '4 hours', NOW() - INTERVAL '3 hours'),

-- Completed, 1 hour ago
('770e8400-e29b-41d4-a716-446655440004', 'fleet-001'::UUID, 'M-20260505-004',
 '660e8400-e29b-41d4-a716-446655440001'::UUID,
 '550e8400-e29b-41d4-a716-446655440001'::UUID,
 'completed', 'normal',
 '{"lat": 37.6000, "lng": -122.5000, "address": "Warehouse A"}'::JSONB,
 '{"lat": 37.8000, "lng": -122.3000, "address": "Store B"}'::JSONB,
 50000, 100, NOW() - INTERVAL '6 hours', NOW() - INTERVAL '5 hours'),

-- Cancelled
('770e8400-e29b-41d4-a716-446655440005', 'fleet-001'::UUID, 'M-20260505-005',
 NULL, NULL,
 'cancelled', 'low',
 '{"lat": 37.5000, "lng": -122.6000, "address": "Location X"}'::JSONB,
 '{"lat": 37.9000, "lng": -122.1000, "address": "Location Y"}'::JSONB,
 100000, 0, NOW() - INTERVAL '24 hours', NULL),

-- 6-20: more missions with various statuses and dates
...
```

### Sample Mission Stops (60 records)

For each of the 20 missions, create 2-5 stops with varying statuses:

```sql
-- For mission M-20260505-003 (66% complete):
INSERT INTO mission_stops (id, mission_id, stop_order, address, status, arrived_at, departed_at) VALUES
('880e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440003'::UUID, 1,
 '150 Van Ness, SF', 'completed', NOW() - INTERVAL '3 hours', NOW() - INTERVAL '2.5 hours'),

('880e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003'::UUID, 2,
 '200 Oak Ave, Oakland', 'completed', NOW() - INTERVAL '1 hour', NOW() - INTERVAL '30 minutes'),

('880e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440003'::UUID, 3,
 '300 Main St, Berkeley', 'pending', NULL, NULL);
```

### Sample Driver Performance Daily (30 records for 1 driver)

```sql
-- For driver John Smith, last 30 days of metrics
INSERT INTO driver_performance_daily (
  driver_id, date, deliveries_count, on_time_count, late_count,
  harsh_braking_count, idling_minutes, fuel_efficiency_liters_per_100km,
  safety_score, efficiency_score, overall_score
) VALUES
-- Recent: 5 deliveries, 4 on-time, good scores
('550e8400-e29b-41d4-a716-446655440001'::UUID, CURRENT_DATE, 5, 4, 1,
 1, 15, 32.5, 95, 88, 92),

('550e8400-e29b-41d4-a716-446655440001'::UUID, CURRENT_DATE - INTERVAL '1 day', 6, 6, 0,
 0, 12, 31.0, 98, 92, 95),

-- ... 28 more days of similar data
```

---

## Validation Test Queries

Run these queries after migration to verify success:

```sql
-- 1. Table structure verification
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' AND table_name IN (
  'drivers', 'trucks', 'missions', 'mission_stops', 
  'mission_events', 'mission_disputes', 'driver_performance_daily'
)
ORDER BY table_name;
-- Expected: 7 rows

-- 2. Primary key verification
SELECT table_name, constraint_type FROM information_schema.table_constraints
WHERE table_schema='public' AND constraint_type='PRIMARY KEY'
ORDER BY table_name;
-- Expected: 7 rows (one per table)

-- 3. Foreign key verification
SELECT constraint_name, table_name, column_name 
FROM information_schema.key_column_usage
WHERE table_schema='public' AND constraint_name LIKE '%fk%'
ORDER BY table_name;
-- Expected: >10 rows (driver FKs, truck FKs, etc.)

-- 4. Index count
SELECT COUNT(*) as index_count FROM pg_indexes 
WHERE schemaname='public';
-- Expected: ≥25

-- 5. View verification
SELECT table_name FROM information_schema.views 
WHERE table_schema='public' AND table_name IN (
  'driver_aggregate_stats', 'truck_aggregate_stats'
);
-- Expected: 2 rows

-- 6. Data sample verification
SELECT COUNT(*) as driver_count FROM drivers WHERE status='active';
SELECT COUNT(*) as active_mission_count FROM missions WHERE status='enroute';
SELECT COUNT(*) as completed_stops FROM mission_stops WHERE status='completed';
-- Expected: >0 for each
```

---

## Success Metrics

After deploying sample data and running tests:

| Metric | Target | Query | Pass? |
|--------|--------|-------|-------|
| Tables created | 7 | SELECT COUNT(*) FROM information_schema.tables WHERE... | ✓ |
| Primary keys | 7 | SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_type='PRIMARY KEY' | ✓ |
| Foreign keys | ≥10 | SELECT COUNT(*) FROM information_schema.key_column_usage WHERE... | ✓ |
| Indexes | ≥25 | SELECT COUNT(*) FROM pg_indexes WHERE schemaname='public' | ✓ |
| Views | 2 | SELECT COUNT(*) FROM information_schema.views WHERE... | ✓ |
| Driver records | ≥5 | SELECT COUNT(*) FROM drivers | ✓ |
| Truck records | ≥10 | SELECT COUNT(*) FROM trucks | ✓ |
| Mission records | ≥20 | SELECT COUNT(*) FROM missions | ✓ |
| Stop records | ≥60 | SELECT COUNT(*) FROM mission_stops | ✓ |
| Performance daily | ≥30 | SELECT COUNT(*) FROM driver_performance_daily | ✓ |
| Data parity | 99.99% | Manual verification of old vs new schema | ✓ |
| Migration time | <5 min | Benchmark migrations 0009, 0010, backfill | ✓ |
| Latency p95 | <200ms | Load test with ab or k6 | ✓ |
| Rollback time | <5 min | Rollback procedure test | ✓ |

---

**Document Version**: 1.0  
**Created**: 2026-05-05  
**Updated**: [ongoing, after each validation cycle]
