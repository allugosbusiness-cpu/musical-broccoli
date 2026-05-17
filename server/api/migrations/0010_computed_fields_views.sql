-- ============================================================
-- Materialized Views & Computed Field Setup
-- Fleet Management v2.0 - Part 2
-- ============================================================

-- ============================================================
-- FUNCTION: Compute driver performance mark
-- ============================================================
CREATE OR REPLACE FUNCTION compute_driver_performance_mark(driver_id UUID)
RETURNS NUMERIC AS $$
DECLARE
  on_time_pct NUMERIC;
  safety_score NUMERIC;
  efficiency_score NUMERIC;
  performance_mark NUMERIC;
BEGIN
  -- Calculate on-time percentage (last 30 days)
  SELECT COALESCE(
    COUNT(CASE WHEN dpm.on_time_count > 0 THEN 1 END)::NUMERIC / 
    NULLIF(COUNT(*), 0) * 100,
    0
  ) INTO on_time_pct
  FROM driver_performance_daily dpm
  WHERE dpm.driver_id = driver_id
    AND dpm.date >= CURRENT_DATE - INTERVAL '30 days';
  
  -- Get average safety score (last 30 days)
  SELECT COALESCE(AVG(dpm.safety_score), 0)
  INTO safety_score
  FROM driver_performance_daily dpm
  WHERE dpm.driver_id = driver_id
    AND dpm.date >= CURRENT_DATE - INTERVAL '30 days';
  
  -- Get average efficiency score (last 30 days)
  SELECT COALESCE(AVG(dpm.efficiency_score), 0)
  INTO efficiency_score
  FROM driver_performance_daily dpm
  WHERE dpm.driver_id = driver_id
    AND dpm.date >= CURRENT_DATE - INTERVAL '30 days';
  
  -- Weighted calculation: on_time (40%), safety (30%), efficiency (30%)
  performance_mark := ROUND(
    (on_time_pct * 0.4 + safety_score * 0.3 + efficiency_score * 0.3)::NUMERIC,
    2
  );
  
  RETURN LEAST(100, GREATEST(0, performance_mark));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================
-- FUNCTION: Compute mission progress percentage
-- ============================================================
CREATE OR REPLACE FUNCTION compute_mission_progress(mission_id UUID)
RETURNS NUMERIC AS $$
DECLARE
  total_stops INTEGER;
  completed_stops INTEGER;
  progress NUMERIC;
BEGIN
  SELECT COUNT(*) INTO total_stops
  FROM mission_stops
  WHERE mission_id = mission_id;
  
  SELECT COUNT(*) INTO completed_stops
  FROM mission_stops
  WHERE mission_id = mission_id
    AND status = 'completed';
  
  IF total_stops = 0 THEN
    RETURN 0;
  END IF;
  
  progress := ROUND((completed_stops::NUMERIC / total_stops) * 100, 2);
  RETURN LEAST(100, progress);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================
-- FUNCTION: Compute mission distance remaining (stub)
-- Note: Requires route polyline and current location
-- ============================================================
CREATE OR REPLACE FUNCTION compute_mission_distance_remaining(mission_id UUID)
RETURNS NUMERIC AS $$
DECLARE
  total_distance NUMERIC;
  distance_travelled NUMERIC;
  distance_remaining NUMERIC;
BEGIN
  -- Get mission total distance
  SELECT m.distance_total_m INTO total_distance
  FROM missions m
  WHERE m.id = mission_id;
  
  -- Calculate distance travelled (sum of completed stops + partial)
  -- Stub: simplified to use stops count
  distance_travelled := (
    SELECT COUNT(*) * 5000  -- Estimate ~5km per stop for demo
    FROM mission_stops
    WHERE mission_id = mission_id
      AND status = 'completed'
  );
  
  distance_remaining := GREATEST(0, COALESCE(total_distance, 0) - COALESCE(distance_travelled, 0));
  
  RETURN distance_remaining;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================
-- FUNCTION: Update driver computed fields
-- ============================================================
CREATE OR REPLACE FUNCTION update_driver_computed_fields()
RETURNS VOID AS $$
BEGIN
  UPDATE drivers d
  SET 
    performance_mark = compute_driver_performance_mark(d.id),
    deliveries_count = (
      SELECT COUNT(DISTINCT ms.id)
      FROM mission_stops ms
      JOIN missions m ON ms.mission_id = m.id
      WHERE m.driver_id = d.id
        AND ms.status = 'completed'
        AND m.completed_at >= NOW() - INTERVAL '30 days'
    ),
    last_active_at = (
      SELECT MAX(m.updated_at)
      FROM missions m
      WHERE m.driver_id = d.id
    )
  WHERE d.status = 'active';
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- FUNCTION: Update mission computed fields
-- ============================================================
CREATE OR REPLACE FUNCTION update_mission_computed_fields()
RETURNS VOID AS $$
BEGIN
  UPDATE missions m
  SET 
    progress_pct = compute_mission_progress(m.id),
    distance_remaining_m = compute_mission_distance_remaining(m.id),
    updated_at = NOW()
  WHERE m.status IN ('enroute', 'paused');
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SCHEDULED JOB: Nightly aggregation refresh
-- (Use pg_cron extension in production)
-- ============================================================
-- SELECT cron.schedule('refresh_driver_stats', '0 2 * * *', 'REFRESH MATERIALIZED VIEW CONCURRENTLY driver_aggregate_stats');
-- SELECT cron.schedule('refresh_truck_stats', '0 2 * * *', 'REFRESH MATERIALIZED VIEW CONCURRENTLY truck_aggregate_stats');
-- SELECT cron.schedule('update_computed_fields', '*/5 * * * *', 'SELECT update_mission_computed_fields(); SELECT update_driver_computed_fields();');

-- ============================================================
-- INDEXES for computed fields queries
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_drivers_performance ON drivers(performance_mark DESC);
CREATE INDEX IF NOT EXISTS idx_drivers_deliveries ON drivers(deliveries_count DESC);
CREATE INDEX IF NOT EXISTS idx_missions_progress ON missions(progress_pct);
CREATE INDEX IF NOT EXISTS idx_missions_remaining_distance ON missions(distance_remaining_m);

-- ============================================================
-- MANUAL REFRESH PROCEDURES (for now, until pg_cron)
-- ============================================================
COMMENT ON FUNCTION compute_driver_performance_mark(UUID) IS 'Compute driver performance score 0-100 from daily metrics';
COMMENT ON FUNCTION compute_mission_progress(UUID) IS 'Compute mission progress as percentage of completed stops';
COMMENT ON FUNCTION update_driver_computed_fields() IS 'Nightly batch update of all driver computed fields';
COMMENT ON FUNCTION update_mission_computed_fields() IS 'Frequent update of active mission progress and distance';
