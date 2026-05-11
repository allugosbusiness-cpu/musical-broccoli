#!/bin/bash
# ============================================================
# Backfill Script: Migrate existing data to new schema v2.0
# Fleet Management - Data Migration & Backfill
# ============================================================
# Usage: ./backfill_scripts.sh [--dry-run] [--fleet-id UUID]
# ============================================================

set -e

DRY_RUN=${1:-"--dry-run"}
FLEET_ID=${2:-"00000000-0000-0000-0000-000000000000"}

echo "=========================================="
echo "Fleet Management Data Backfill Script"
echo "=========================================="
echo "Dry Run: $DRY_RUN"
echo "Fleet ID: $FLEET_ID"
echo ""

# Database connection (adjust as needed)
PGHOST=${DB_HOST:-localhost}
PGPORT=${DB_PORT:-5432}
PGDATABASE=${DB_NAME:-fleet_db}
PGUSER=${DB_USER:-postgres}
PGPASSWORD=${DB_PASSWORD:-password}

export PGHOST PGPORT PGDATABASE PGUSER PGPASSWORD

# ============================================================
# STEP 1: Validate prerequisites
# ============================================================
echo "[1/8] Validating schema..."
if ! psql -c "SELECT 1 FROM information_schema.tables WHERE table_name='drivers' LIMIT 1;" > /dev/null 2>&1; then
  echo "ERROR: New schema not found. Run migrations first."
  exit 1
fi
echo "✓ New schema tables exist"

# ============================================================
# STEP 2: Backfill DRIVERS from existing users/truck data
# ============================================================
echo ""
echo "[2/8] Backfilling drivers table..."

DRIVERS_SQL="
BEGIN;
-- Create drivers from existing unique user entries
-- Assumption: existing system has driver names in 'driver' column of trucks
INSERT INTO drivers (id, fleet_id, first_name, last_name, phone, email, status, hire_date)
SELECT 
  gen_random_uuid(),
  '$FLEET_ID'::UUID,
  SPLIT_PART(COALESCE(t.driver, 'Unknown Driver'), ' ', 1),
  COALESCE(SPLIT_PART(COALESCE(t.driver, 'Unknown Driver'), ' ', 2), ''),
  NULL,
  NULL,
  'active',
  CURRENT_DATE
FROM (
  SELECT DISTINCT driver FROM trucks WHERE driver IS NOT NULL AND driver != ''
) t
ON CONFLICT (email) DO NOTHING;

COMMIT;
"

if [ "$DRY_RUN" != "--apply" ]; then
  echo "DRY RUN: Would execute:"
  echo "$DRIVERS_SQL"
else
  echo "Executing: Backfill drivers..."
  psql -c "$DRIVERS_SQL"
  echo "✓ Drivers backfilled"
fi

# ============================================================
# STEP 3: Backfill TRUCKS
# ============================================================
echo ""
echo "[3/8] Backfilling trucks table..."

TRUCKS_SQL="
BEGIN;
-- Create trucks from existing truck records
INSERT INTO trucks (
  id, fleet_id, truck_identifier, plate, status, 
  telematics_id, assigned_driver_id, last_latitude, last_longitude
)
SELECT 
  COALESCE(t.id::UUID, gen_random_uuid()),
  '$FLEET_ID'::UUID,
  COALESCE(t.id, 'TRUCK-' || ROW_NUMBER() OVER()),
  t.plate,
  CASE 
    WHEN t.status = 'moving' THEN 'enroute'
    WHEN t.status = 'maintenance' THEN 'maintenance'
    ELSE 'idle'
  END,
  t.id,  -- telematics_id
  NULL,  -- assigned_driver_id (will be linked later)
  (t.coordinates ->> 'lat')::NUMERIC,
  (t.coordinates ->> 'lng')::NUMERIC
FROM trucks t
ON CONFLICT (telematics_id) DO NOTHING;

COMMIT;
"

if [ "$DRY_RUN" != "--apply" ]; then
  echo "DRY RUN: Would execute:"
  echo "$TRUCKS_SQL"
else
  echo "Executing: Backfill trucks..."
  psql -c "$TRUCKS_SQL"
  echo "✓ Trucks backfilled"
fi

# ============================================================
# STEP 4: Backfill MISSIONS (from existing truck trips)
# ============================================================
echo ""
echo "[4/8] Backfilling missions table..."

MISSIONS_SQL="
BEGIN;
-- Create missions from existing truck routes
INSERT INTO missions (
  id, fleet_id, mission_number, truck_id, status,
  origin, destination, progress_pct, created_at
)
SELECT 
  gen_random_uuid(),
  '$FLEET_ID'::UUID,
  'M-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || ROW_NUMBER() OVER(),
  t.id,
  CASE 
    WHEN t.status = 'enroute' THEN 'enroute'
    WHEN t.status = 'delivered' THEN 'completed'
    ELSE 'planned'
  END,
  jsonb_build_object(
    'lat', (t.origin_coordinates ->> 'lat')::NUMERIC,
    'lng', (t.origin_coordinates ->> 'lng')::NUMERIC,
    'address', COALESCE(t.origin, 'Start')
  ),
  jsonb_build_object(
    'lat', (t.destination_coordinates ->> 'lat')::NUMERIC,
    'lng', (t.destination_coordinates ->> 'lng')::NUMERIC,
    'address', COALESCE(t.destination, 'End')
  ),
  t.progress,
  t.created_at
FROM trucks t
WHERE t.status IN ('moving', 'delivered')
  AND t.origin_coordinates IS NOT NULL
  AND t.destination_coordinates IS NOT NULL;

COMMIT;
"

if [ "$DRY_RUN" != "--apply" ]; then
  echo "DRY RUN: Would execute:"
  echo "$MISSIONS_SQL"
else
  echo "Executing: Backfill missions..."
  psql -c "$MISSIONS_SQL"
  echo "✓ Missions backfilled"
fi

# ============================================================
# STEP 5: Backfill MISSION_STOPS from CHECKPOINTS
# ============================================================
echo ""
echo "[5/8] Backfilling mission_stops table..."

STOPS_SQL="
BEGIN;
-- Create mission stops from existing checkpoints
INSERT INTO mission_stops (id, mission_id, stop_order, address, status)
SELECT 
  COALESCE(c.id::UUID, gen_random_uuid()),
  m.id,
  ROW_NUMBER() OVER (PARTITION BY c.truck_id ORDER BY c.timestamp),
  c.name,
  CASE 
    WHEN c.status = 'done' THEN 'completed'
    WHEN c.status = 'active' THEN 'pending'
    ELSE 'pending'
  END
FROM checkpoints c
JOIN trucks t ON c.truck_id = t.id
JOIN missions m ON t.id = m.truck_id
WHERE c.created_at >= NOW() - INTERVAL '90 days';

COMMIT;
"

if [ "$DRY_RUN" != "--apply" ]; then
  echo "DRY RUN: Would execute:"
  echo "$STOPS_SQL"
else
  echo "Executing: Backfill mission_stops..."
  psql -c "$STOPS_SQL"
  echo "✓ Mission stops backfilled"
fi

# ============================================================
# STEP 6: Compute DELIVERIES_COUNT for drivers
# ============================================================
echo ""
echo "[6/8] Computing driver deliveries..."

DELIVERIES_SQL="
BEGIN;
UPDATE drivers d
SET deliveries_count = (
  SELECT COUNT(DISTINCT ms.id)
  FROM mission_stops ms
  JOIN missions m ON ms.mission_id = m.id
  WHERE m.driver_id = d.id
    AND ms.status = 'completed'
    AND m.completed_at >= NOW() - INTERVAL '30 days'
);
COMMIT;
"

if [ "$DRY_RUN" != "--apply" ]; then
  echo "DRY RUN: Would execute:"
  echo "$DELIVERIES_SQL"
else
  echo "Executing: Compute deliveries..."
  psql -c "$DELIVERIES_SQL"
  echo "✓ Deliveries computed"
fi

# ============================================================
# STEP 7: Backfill DRIVER_PERFORMANCE_DAILY
# ============================================================
echo ""
echo "[7/8] Backfilling driver_performance_daily..."

PERF_SQL="
BEGIN;
-- Create daily performance records for last 30 days
INSERT INTO driver_performance_daily (
  driver_id, date, deliveries_count, on_time_count, overall_score
)
SELECT 
  d.id,
  generate_series(
    (NOW() - INTERVAL '30 days')::DATE,
    NOW()::DATE,
    '1 day'::INTERVAL
  )::DATE,
  COALESCE(
    COUNT(DISTINCT ms.id) FILTER (WHERE ms.status = 'completed'),
    0
  ),
  0,
  ROUND((RANDOM() * 100)::NUMERIC, 2)  -- Placeholder
FROM drivers d
LEFT JOIN missions m ON d.id = m.driver_id
LEFT JOIN mission_stops ms ON m.id = ms.mission_id
GROUP BY d.id;

COMMIT;
"

if [ "$DRY_RUN" != "--apply" ]; then
  echo "DRY RUN: Would execute:"
  echo "$PERF_SQL"
else
  echo "Executing: Backfill performance metrics..."
  psql -c "$PERF_SQL"
  echo "✓ Performance metrics backfilled"
fi

# ============================================================
# STEP 8: Refresh materialized views
# ============================================================
echo ""
echo "[8/8] Refreshing materialized views..."

VIEWS_SQL="
REFRESH MATERIALIZED VIEW CONCURRENTLY driver_aggregate_stats;
REFRESH MATERIALIZED VIEW CONCURRENTLY truck_aggregate_stats;
"

if [ "$DRY_RUN" != "--apply" ]; then
  echo "DRY RUN: Would execute:"
  echo "$VIEWS_SQL"
else
  echo "Executing: Refresh views..."
  psql -c "$VIEWS_SQL"
  echo "✓ Materialized views refreshed"
fi

# ============================================================
# VALIDATION
# ============================================================
echo ""
echo "=========================================="
echo "Validation Checks"
echo "=========================================="

psql -c "
SELECT 
  (SELECT COUNT(*) FROM drivers) as drivers_count,
  (SELECT COUNT(*) FROM trucks) as trucks_count,
  (SELECT COUNT(*) FROM missions) as missions_count,
  (SELECT COUNT(*) FROM mission_stops) as stops_count;
"

echo ""
echo "=========================================="
echo "Backfill Summary"
echo "=========================================="
if [ "$DRY_RUN" != "--apply" ]; then
  echo "DRY RUN COMPLETE - No data was modified."
  echo ""
  echo "To execute the backfill, run:"
  echo "  ./backfill_scripts.sh --apply"
else
  echo "BACKFILL COMPLETE!"
  echo ""
  echo "Next steps:"
  echo "1. Verify data integrity"
  echo "2. Test dual-write phase (if applicable)"
  echo "3. Run acceptance tests"
  echo "4. Monitor API metrics"
fi

echo ""
