# Fleet Management v2.0 - Schema Migration Rollout Plan
## Safe, Staged Deployment of New Data Model

**Date**: May 2026  
**Version**: 2.0.0  
**Audience**: DevOps, Backend Engineers, Product Managers  
**Risk Level**: Medium (new schema, dual-write phase, feature flags)  
**Rollback Time**: <30 minutes

---

## Executive Summary

This plan deploys a new database schema (Drivers, Trucks, Missions as separate entities) without disrupting existing services. Strategy:

1. **Dual-Write Phase (48-72 hours)**: Write to both old + new schemas simultaneously. Verify data parity.
2. **Read Phase (72 hours)**: Gradually enable reads from new schema via feature flags.
3. **Sunset Phase (2-4 weeks)**: Monitor, then decommission old schema.

Success Criteria:
- 99.99%+ data parity between old and new schemas
- Zero downtime
- Automatic rollback on metrics violation (exception rate >0.1/sec, latency >2s p95)

---

## Stage 1: Pre-Flight Validation (Week Before)

**Objective**: Ensure staging environment mirrors production. Validate migrations run cleanly.

### Tasks

| Task | Owner | Status |
|------|-------|--------|
| Apply migrations to staging DB | DevOps | TODO |
| Backfill with production data snapshot | DevOps | TODO |
| Run acceptance tests | QA | TODO |
| Load test (1000 req/sec) | Performance | TODO |
| Verify rollback procedures | DevOps | TODO |

### Validation Queries

```sql
-- Run on staging after migration
SELECT 'drivers' as table_name, COUNT(*) as count FROM drivers
UNION ALL
SELECT 'trucks', COUNT(*) FROM trucks
UNION ALL
SELECT 'missions', COUNT(*) FROM missions
UNION ALL
SELECT 'mission_stops', COUNT(*) FROM mission_stops;

-- Verify constraints
SELECT constraint_name FROM information_schema.table_constraints 
WHERE table_name='drivers' AND constraint_type='UNIQUE';

-- Verify indexes
SELECT indexname FROM pg_indexes WHERE tablename='missions' 
ORDER BY indexname;
```

### Monitoring Setup

- Create Grafana dashboard (see `monitoring_dashboard.json`)
- Configure PagerDuty for critical alerts
- Set baseline metrics (latency, throughput, error rate)

---

## Stage 2: Deploy New Schema to Production (Day 1)

**Objective**: Create new tables without touching old data. Pure addition, no disruption.

### Pre-Deployment Checks (1 hour before)

```bash
# Verify DB connection
psql -h <prod-db> -U <admin> -d fleet_db -c "SELECT version();"

# Backup production DB
pg_dump -h <prod-db> -U <admin> fleet_db > fleet_db_backup_2026-05-05.sql

# Verify backup
file fleet_db_backup_2026-05-05.sql
du -h fleet_db_backup_2026-05-05.sql  # Should be >1GB
```

### Deployment

**Time Window**: 2-3 AM (low traffic)

```bash
# SSH to prod DB server
ssh prod-db-01

# Run migrations (in transaction, auto-rollback on error)
cd /app/fleet_management/server/api/migrations

# Apply 0009: Create new schema
psql -h localhost -U postgres fleet_db < 0009_create_drivers_trucks_missions_schema_v2.sql

# Apply 0010: Create computed field functions
psql -h localhost -U postgres fleet_db < 0010_computed_fields_views.sql

# Verify tables created
psql -h localhost -U postgres fleet_db -c "
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' 
ORDER BY table_name;"
```

**Expected Output**:
```
admin_audit_logs
driver_performance_daily
drivers
driver_aggregate_stats (view)
mission_disputes
mission_events
mission_stops
missions
truck_aggregate_stats (view)
trucks
```

### Rollback (if needed)

```bash
# Drop new tables (safe: no old data touched)
psql -h localhost -U postgres fleet_db << EOF
DROP VIEW truck_aggregate_stats;
DROP VIEW driver_aggregate_stats;
DROP TABLE admin_audit_logs;
DROP TABLE driver_performance_daily;
DROP TABLE mission_disputes;
DROP TABLE mission_events;
DROP TABLE mission_stops;
DROP TABLE missions;
DROP TABLE trucks;
DROP TABLE drivers;
EOF

# Alert on-call: "Schema migration rolled back, old schema unaffected"
```

### Post-Deployment

- Verify all tables exist with correct structure
- Confirm indexes created (should see 25+ indexes)
- Test constraint violations (e.g., insert duplicate email → should fail)

---

## Stage 3: Backfill Data (Day 1, after tables created)

**Objective**: Populate new tables from existing data. Read-only backfill, no writes to new schema yet.

### Run Backfill Script

```bash
# Test run (dry-run, shows SQL without executing)
./backfill_data_v2.sh --dry-run --fleet-id 00000000-0000-0000-0000-000000000000

# Verify output looks reasonable, then apply
./backfill_data_v2.sh --apply --fleet-id 00000000-0000-0000-0000-000000000000

# Monitor progress
watch -n 5 "psql -c 'SELECT (SELECT COUNT(*) FROM drivers) as drivers, (SELECT COUNT(*) FROM trucks) as trucks, (SELECT COUNT(*) FROM missions) as missions;'"
```

### Validation After Backfill

```sql
-- Verify counts match old schema
SELECT 
  (SELECT COUNT(*) FROM old_trucks) as old_truck_count,
  (SELECT COUNT(*) FROM trucks) as new_truck_count,
  (SELECT COUNT(*) FROM old_driver_records) as old_driver_count,
  (SELECT COUNT(*) FROM drivers) as new_driver_count;

-- Verify sample data integrity
SELECT id, truck_identifier, plate FROM trucks LIMIT 5;
SELECT id, first_name, last_name, license_number FROM drivers LIMIT 5;
```

### Rollback (if data mismatch detected)

```bash
# If counts don't match within 1%, rollback:
psql -h localhost -U postgres fleet_db << EOF
DELETE FROM admin_audit_logs;
DELETE FROM driver_performance_daily;
DELETE FROM mission_disputes;
DELETE FROM mission_events;
DELETE FROM mission_stops;
DELETE FROM missions;
DELETE FROM trucks;
DELETE FROM drivers;
EOF

# Alert: "Backfill data mismatch detected, new tables cleared for retry"
```

---

## Stage 4: Enable Dual-Write Phase (Day 1, Evening)

**Objective**: New code writes to both old + new schemas simultaneously. No reads from new schema yet.

### Deploy Code with Feature Flags

```python
# Deploy updated services_v2.py and views_v2.py with dual-write logic

# In create_mission():
def create_mission(...):
    # Write to OLD schema (backward compat)
    old_truck_trip = OldTruckTrip.objects.create(...)
    
    # Write to NEW schema (if flag enabled)
    if settings.FEATURE_FLAGS['new_schema_write']:
        new_mission = Mission.objects.create(...)
        MissionEvent.objects.create(...)  # Audit trail
    
    return old_truck_trip

# In driver update:
def update_driver(...):
    # Always write to old schema first
    old_driver_record.update(...)
    
    # Then new schema if enabled
    if settings.FEATURE_FLAGS['new_schema_write']:
        new_driver = Driver.objects.update(...)
    
    return response
```

### Enable Feature Flag

```bash
# Update Django settings or Redis key
# Option 1: Django settings (requires code restart)
# Option 2: Redis (no restart needed)

redis-cli set fleet_manager:feature_flags:new_schema_write true

# Verify in app logs
tail -f /var/log/fleet_manager/app.log | grep "dual-write"
```

### Monitoring During Dual-Write (48-72 hours)

**Check every 30 minutes**:

```python
# Query to verify dual-write parity
import psycopg2

conn = psycopg2.connect("dbname=fleet_db user=postgres")
cur = conn.cursor()

# Check mission counts
cur.execute("SELECT COUNT(*) FROM old_truck_trips WHERE created_at > NOW() - INTERVAL '1 hour';")
old_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM missions WHERE created_at > NOW() - INTERVAL '1 hour';")
new_count = cur.fetchone()[0]

parity_pct = (min(old_count, new_count) / max(old_count, new_count) * 100) if max(old_count, new_count) > 0 else 100

print(f"Old: {old_count}, New: {new_count}, Parity: {parity_pct:.2f}%")

if parity_pct < 99.99:
    alert("CRITICAL: Dual-write parity below 99.99%")
    rollback()
```

**Expected Logs**:
```
2026-05-05 14:23:45 [fleet_manager] dual-write enabled, new_schema_write=true
2026-05-05 14:24:10 [fleet_manager] CREATE mission M-001: old schema (success), new schema (success)
2026-05-05 14:24:45 [fleet_manager] PATCH driver D-123: old schema (success), new schema (success)
...
2026-05-05 18:00:00 [fleet_manager] Dual-write parity check: 99.99% (4500/4500 records match)
```

### Rollback (if parity < 99.99%)

```bash
# Disable dual-write immediately
redis-cli set fleet_manager:feature_flags:new_schema_write false

# Clear new schema data
psql << EOF
DELETE FROM mission_events;
DELETE FROM mission_stops;
DELETE FROM missions;
DELETE FROM admin_audit_logs;
EOF

# Alert: "Parity check failed, dual-write disabled, new schema cleared"
```

---

## Stage 5: Enable Reads from New Schema (Day 4, Morning)

**Objective**: Gradually shift read queries to new schema. Use feature flag for gradual rollout.

### Deploy Read-Side Changes

```python
# In DriverService.list_drivers():
def list_drivers(fleet_id, status=None):
    if settings.FEATURE_FLAGS['new_schema_read']:
        # Read from new schema
        return Driver.objects.filter(fleet_id=fleet_id, status=status)
    else:
        # Read from old schema
        return OldDriver.objects.filter(fleet_id=fleet_id, status=status)

# In MissionService.get_mission():
def get_mission(mission_id):
    if settings.FEATURE_FLAGS['new_schema_read']:
        # Use new schema query
        return Mission.objects.prefetch_related('stops_detail').get(id=mission_id)
    else:
        # Use old schema query
        return OldTruckTrip.objects.get(id=mission_id)
```

### Rollout Wave 1: 10% of Customers (Pilot Fleet)

```bash
# Select a small, stable customer (e.g., one internal fleet, or fleet with <50 vehicles)
PILOT_FLEET_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Update feature flag for pilot only
redis-cli set fleet_manager:feature_flags:new_schema_read:${PILOT_FLEET_ID} true

# Monitor for 24 hours
```

**Metrics to Watch**:
- Exception rate: should stay at 0
- Latency p95: should be <500ms (same as before)
- Data consistency: sample queries should match between old/new schema
- User complaints: should be zero

**Monitoring Commands**:

```bash
# Check latency
curl -s http://monitoring:3000/api/metrics | jq '.latency_p95'

# Check errors
curl -s http://monitoring:3000/api/metrics | jq '.exception_rate'

# Sample data validation
curl http://api:8000/api/v1/drivers?fleet_id=${PILOT_FLEET_ID} | jq '.results[0]'
# Compare with old schema manually
```

### Automatic Rollback Trigger for Pilot

If any metric fails:
- Exception rate > 0.1/sec → disable feature flag for fleet
- Latency p95 > 2 seconds → disable feature flag for fleet
- Error rate > 1% → disable feature flag for fleet

```python
# In monitoring task (runs every 5 min)
def check_read_feature_flag_health(fleet_id):
    metrics = get_metrics(fleet_id)
    
    if metrics['exception_rate'] > 0.001 or metrics['latency_p95'] > 2000:
        logger.critical(f"Read feature flag health check failed for {fleet_id}")
        redis.delete(f"fleet_manager:feature_flags:new_schema_read:{fleet_id}")
        alert("Auto-rollback: New schema read disabled for fleet due to metrics")
```

### Rollout Wave 2: 50% of Customers (Day 5)

Once pilot passes 24-hour health check:

```bash
# Get list of all fleet IDs
FLEET_IDS=$(curl -s http://api:8000/api/v1/fleets | jq -r '.results[].id')

# Calculate 50%
TOTAL=$(echo "$FLEET_IDS" | wc -l)
HALF=$((TOTAL / 2))

# Enable for first 50%
i=0
for fleet_id in $FLEET_IDS; do
  if [ $i -lt $HALF ]; then
    redis-cli set fleet_manager:feature_flags:new_schema_read:${fleet_id} true
  fi
  i=$((i + 1))
done

echo "Enabled new schema read for $HALF / $TOTAL fleets"
```

**Monitor for 24 hours**:
- Repeat health checks
- Watch error logs for pattern changes
- Compare latency between enabled/disabled fleets

### Rollout Wave 3: 100% of Customers (Day 6)

```bash
# Global enable
redis-cli set fleet_manager:feature_flags:new_schema_read true

echo "New schema read enabled globally"

# Continue monitoring for 48 hours
```

---

## Stage 6: General Availability (Day 8)

**Objective**: New schema is now the primary system. Announce GA.

### Checklist

- [ ] All reads using new schema for 48+ hours
- [ ] Data consistency confirmed across all fleets
- [ ] Zero exceptions attributed to new schema
- [ ] API latency stable (<500ms p95)
- [ ] Backup of old schema data retained (30 days)

### Disable Old Schema Writes (Optional, Day 15+)

```bash
# After 1 week of GA, disable writes to old schema (if desired)
redis-cli set fleet_manager:feature_flags:old_schema_write false

# Monitor for any breakage, should be none
```

### Decommission Old Schema (Optional, Day 30+)

```bash
# After 30 days with new schema only, drop old tables
psql << EOF
-- Backup old schema first
CREATE SCHEMA old_schema_archive AS SELECT * FROM information_schema.tables;

-- Drop old tables (one-way operation!)
DROP TABLE IF EXISTS old_truck_trips CASCADE;
DROP TABLE IF EXISTS old_checkpoints CASCADE;
DROP TABLE IF EXISTS old_driver_records CASCADE;
DROP TABLE IF EXISTS old_alerts CASCADE;

VACUUM ANALYZE;  -- Reclaim space
EOF

echo "Old schema decommissioned"
```

---

## Rollback Procedures

### Scenario: Data Parity Check Fails During Dual-Write

**Time to Rollback**: <5 minutes

```bash
# 1. Disable dual-write immediately
redis-cli set fleet_manager:feature_flags:new_schema_write false

# 2. Clear new schema data
psql << EOF
TRUNCATE TABLE mission_events CASCADE;
TRUNCATE TABLE mission_stops CASCADE;
TRUNCATE TABLE missions CASCADE;
TRUNCATE TABLE admin_audit_logs CASCADE;
EOF

# 3. Alert on-call
pagerduty_trigger(
  service="Fleet Manager",
  severity="critical",
  title="Schema migration: parity check failed, new schema disabled",
  details="Dual-write phase aborted. Old schema remains intact."
)

# 4. Investigate root cause
# - Compare sample records
# - Check logs for transformation errors
# - Fix code bugs
```

### Scenario: Exception Rate Spikes During Read Phase

**Time to Rollback**: <1 minute (automatic)

```python
# Monitoring task will automatically:
# 1. Detect exception_rate > 0.1/sec
# 2. Disable feature flag: redis.delete('fleet_manager:feature_flags:new_schema_read:*')
# 3. Routes all reads back to old schema
# 4. Sends alert to on-call

# Manual recovery:
redis-cli set fleet_manager:feature_flags:new_schema_read false
# App will immediately revert to old schema reads
```

### Scenario: Full Database Corruption

**Time to Rollback**: <30 minutes (restore from backup)

```bash
# 1. Stop the application
systemctl stop fleet_manager_api

# 2. Restore production DB from backup (pre-migration)
pg_restore -h <prod-db> -U postgres -d fleet_db fleet_db_backup_2026-05-05.sql

# 3. Verify old schema is intact
psql -c "SELECT COUNT(*) FROM old_truck_trips;"  # Should show count

# 4. Restart application
systemctl start fleet_manager_api

# 5. Alert stakeholders
email_broadcast("Database restored from backup. Old schema active. Zero data loss.")
```

---

## Monitoring Dashboard Queries

### Query 1: Data Parity (during dual-write)

```sql
-- Run every 30 min during stages 4-5
SELECT
  'missions' as entity,
  (SELECT COUNT(*) FROM old_truck_trips WHERE created_at > NOW() - INTERVAL '1 hour') as old_count,
  (SELECT COUNT(*) FROM missions WHERE created_at > NOW() - INTERVAL '1 hour') as new_count,
  ROUND(
    MIN(
      (SELECT COUNT(*) FROM old_truck_trips WHERE created_at > NOW() - INTERVAL '1 hour'),
      (SELECT COUNT(*) FROM missions WHERE created_at > NOW() - INTERVAL '1 hour')
    )::numeric / GREATEST(
      (SELECT COUNT(*) FROM old_truck_trips WHERE created_at > NOW() - INTERVAL '1 hour'),
      (SELECT COUNT(*) FROM missions WHERE created_at > NOW() - INTERVAL '1 hour'),
      1
    ) * 100, 2
  ) as parity_pct
UNION ALL
SELECT
  'drivers',
  (SELECT COUNT(*) FROM old_driver_records WHERE updated_at > NOW() - INTERVAL '1 hour'),
  (SELECT COUNT(*) FROM drivers WHERE updated_at > NOW() - INTERVAL '1 hour'),
  ...
```

### Query 2: Performance Comparison

```sql
-- Compare API latency before/after new schema reads enabled
SELECT
  DATE_TRUNC('minute', timestamp) as minute,
  SUM(CASE WHEN schema='old' THEN 1 ELSE 0 END) as old_requests,
  SUM(CASE WHEN schema='new' THEN 1 ELSE 0 END) as new_requests,
  ROUND(AVG(CASE WHEN schema='old' THEN latency_ms ELSE NULL END), 2) as old_avg_latency,
  ROUND(AVG(CASE WHEN schema='new' THEN latency_ms ELSE NULL END), 2) as new_avg_latency
FROM api_metrics
WHERE timestamp > NOW() - INTERVAL '4 hours'
GROUP BY DATE_TRUNC('minute', timestamp)
ORDER BY minute DESC;
```

### Query 3: Error Rate by Schema

```sql
SELECT
  DATE_TRUNC('minute', timestamp) as minute,
  schema,
  COUNT(*) as total_requests,
  SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as errors,
  ROUND(
    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2
  ) as error_pct
FROM api_metrics
WHERE timestamp > NOW() - INTERVAL '4 hours'
GROUP BY DATE_TRUNC('minute', timestamp), schema
ORDER BY minute DESC, schema;
```

---

## Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| Data Parity | ≥99.99% | Query counts match old/new schema |
| Uptime | 100% | Zero unplanned downtime during migration |
| Latency (p95) | <500ms | Monitoring dashboard / APM tool |
| Exception Rate | <0.1/sec | Application metrics / Sentry |
| Error Rate | <0.1% | HTTP status codes from API |
| Rollback Time | <5 min | Manual + automatic tests |

---

## Timeline Summary

| Date | Stage | Status |
|------|-------|--------|
| May 2 | Pre-flight validation | ⏳ TODO |
| May 3 02:00 UTC | Deploy new schema | ⏳ TODO |
| May 3 06:00 UTC | Backfill data | ⏳ TODO |
| May 3 18:00 UTC | Enable dual-write | ⏳ TODO |
| May 4-5 | Monitor parity 48h | ⏳ TODO |
| May 6 10:00 UTC | Enable reads (pilot 10%) | ⏳ TODO |
| May 7 10:00 UTC | Expand reads (50%) | ⏳ TODO |
| May 8 10:00 UTC | Full GA (100%) | ⏳ TODO |
| May 15+ | Optional: disable old writes | ⏳ TODO |
| May 30+ | Optional: decommission old schema | ⏳ TODO |

---

## Contacts

- **DevOps Lead**: [name] ([email])
- **Backend Lead**: [name] ([email])
- **On-Call**: [PagerDuty escalation policy]
- **Escalation**: CTO ([email])

---

## Appendix: Feature Flag Configuration

### Redis Keys

```bash
# Global flags
fleet_manager:feature_flags:new_schema_write = false | true
fleet_manager:feature_flags:new_schema_read = false | true
fleet_manager:feature_flags:old_schema_write = true | false

# Per-fleet flags (if gradual rollout)
fleet_manager:feature_flags:new_schema_read:{fleet_id} = false | true

# Example: Enable new schema read for specific fleet
redis-cli set fleet_manager:feature_flags:new_schema_read:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx true
```

### Django Settings

```python
FEATURE_FLAGS = {
    'new_schema_write': False,  # Default: write to old schema only
    'new_schema_read': False,   # Default: read from old schema only
    'old_schema_write': True,   # Keep enabled during migration
}

# Load from Redis at app startup
def load_feature_flags():
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    
    FEATURE_FLAGS['new_schema_write'] = r.get('fleet_manager:feature_flags:new_schema_write') == b'true'
    FEATURE_FLAGS['new_schema_read'] = r.get('fleet_manager:feature_flags:new_schema_read') == b'true'
    
    return FEATURE_FLAGS
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-05  
**Next Review**: After migration complete (2026-06-05)
