-- ============================================================
-- Fleet Management: Data Model v2.0
-- PostgreSQL Migration - Create Drivers, Trucks, Missions
-- Date: 2026-05-05
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- ============================================================
-- 1. DRIVERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS drivers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fleet_id UUID NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  display_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
  phone TEXT,
  email TEXT,
  license_number TEXT UNIQUE,
  license_state TEXT,
  hire_date DATE,
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'suspended', 'terminated', 'on_leave')),
  on_duty BOOLEAN NOT NULL DEFAULT FALSE,
  achievements JSONB DEFAULT '[]'::jsonb,
  performance_mark NUMERIC(5,2) DEFAULT 0 CHECK (performance_mark >= 0 AND performance_mark <= 100),
  deliveries_count INTEGER DEFAULT 0,
  last_active_at TIMESTAMP WITH TIME ZONE,
  photo_url TEXT,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_drivers_fleet ON drivers(fleet_id);
CREATE INDEX IF NOT EXISTS idx_drivers_status ON drivers(status);
CREATE INDEX IF NOT EXISTS idx_drivers_on_duty ON drivers(on_duty);
CREATE INDEX IF NOT EXISTS idx_drivers_email ON drivers(email);
CREATE INDEX IF NOT EXISTS idx_drivers_license ON drivers(license_number);

-- ============================================================
-- 2. TRUCKS TABLE (Redesigned)
-- ============================================================
CREATE TABLE IF NOT EXISTS trucks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fleet_id UUID NOT NULL,
  truck_identifier TEXT NOT NULL,
  plate TEXT UNIQUE,
  vin TEXT UNIQUE,
  make TEXT,
  model TEXT,
  year INTEGER,
  telematics_id TEXT UNIQUE,
  fuel_capacity_liters NUMERIC(10,2),
  fuel_consumed_liters NUMERIC(14,4) DEFAULT 0,
  odometer_km NUMERIC(14,3) DEFAULT 0,
  kilometers_travelled_km NUMERIC(14,3) DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'idle'
    CHECK (status IN ('idle', 'enroute', 'maintenance', 'decommissioned')),
  is_moving BOOLEAN DEFAULT FALSE,
  last_location GEOGRAPHY(POINT, 4326),
  last_location_ts TIMESTAMP WITH TIME ZONE,
  last_latitude NUMERIC(10,6),
  last_longitude NUMERIC(10,6),
  maintenance_due_date DATE,
  assigned_driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_trucks_fleet ON trucks(fleet_id);
CREATE INDEX IF NOT EXISTS idx_trucks_telem ON trucks(telematics_id);
CREATE INDEX IF NOT EXISTS idx_trucks_status ON trucks(status);
CREATE INDEX IF NOT EXISTS idx_trucks_driver ON trucks(assigned_driver_id);
CREATE INDEX IF NOT EXISTS idx_trucks_plate ON trucks(plate);

-- ============================================================
-- 3. MISSIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS missions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fleet_id UUID NOT NULL,
  mission_number TEXT UNIQUE NOT NULL,
  truck_id UUID REFERENCES trucks(id) ON DELETE SET NULL,
  driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
  created_by_admin_id UUID,
  status TEXT NOT NULL DEFAULT 'planned'
    CHECK (status IN ('planned', 'assigned', 'enroute', 'paused', 'completed', 'cancelled')),
  priority TEXT DEFAULT 'normal'
    CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
  origin JSONB NOT NULL,  -- {lat, lng, address}
  destination JSONB NOT NULL,  -- {lat, lng, address}
  current_location JSONB,  -- {lat, lng, ts}
  route_polyline TEXT,  -- encoded or GeoJSON
  distance_total_m NUMERIC(14,2) DEFAULT 0,
  distance_remaining_m NUMERIC(14,2) DEFAULT 0,
  progress_pct NUMERIC(5,2) DEFAULT 0 CHECK (progress_pct >= 0 AND progress_pct <= 100),
  speed_kmh NUMERIC(8,3),
  eta TIMESTAMP WITH TIME ZONE,
  cargo JSONB,  -- {type, weight_kg, description, special_handling}
  stops JSONB DEFAULT '[]'::jsonb,  -- [{stop_number, address, lat, lng, eta, status, arrived_at}]
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_missions_fleet ON missions(fleet_id);
CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);
CREATE INDEX IF NOT EXISTS idx_missions_truck ON missions(truck_id);
CREATE INDEX IF NOT EXISTS idx_missions_driver ON missions(driver_id);
CREATE INDEX IF NOT EXISTS idx_missions_number ON missions(mission_number);
CREATE INDEX IF NOT EXISTS idx_missions_created ON missions(created_at DESC);

-- ============================================================
-- 4. MISSION STOPS TABLE (Normalized)
-- ============================================================
CREATE TABLE IF NOT EXISTS mission_stops (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
  stop_order INTEGER NOT NULL,
  address TEXT,
  latitude NUMERIC(10,6),
  longitude NUMERIC(10,6),
  status TEXT DEFAULT 'pending'
    CHECK (status IN ('pending', 'completed', 'skipped')),
  arrived_at TIMESTAMP WITH TIME ZONE,
  departed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mission_stops_mission ON mission_stops(mission_id);
CREATE INDEX IF NOT EXISTS idx_mission_stops_status ON mission_stops(status);

-- ============================================================
-- 5. MISSION EVENTS TABLE (Audit/Replay)
-- ============================================================
CREATE TABLE IF NOT EXISTS mission_events (
  id BIGSERIAL PRIMARY KEY,
  mission_id UUID REFERENCES missions(id) ON DELETE CASCADE,
  truck_id UUID REFERENCES trucks(id) ON DELETE SET NULL,
  driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
  event_type TEXT NOT NULL,
  payload JSONB,
  trace_id UUID DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mission_events_mission ON mission_events(mission_id);
CREATE INDEX IF NOT EXISTS idx_mission_events_truck ON mission_events(truck_id);
CREATE INDEX IF NOT EXISTS idx_mission_events_driver ON mission_events(driver_id);
CREATE INDEX IF NOT EXISTS idx_mission_events_type ON mission_events(event_type);
CREATE INDEX IF NOT EXISTS idx_mission_events_created ON mission_events(created_at DESC);

-- ============================================================
-- 6. ADMIN AUDIT LOG
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_audit_logs (
  id BIGSERIAL PRIMARY KEY,
  admin_id UUID NOT NULL,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id UUID,
  old_values JSONB,
  new_values JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_created ON admin_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_audit_resource ON admin_audit_logs(resource_type, resource_id);

-- ============================================================
-- 7. DISPUTES TABLE (Driver complaints)
-- ============================================================
CREATE TABLE IF NOT EXISTS mission_disputes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
  driver_id UUID NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
  stop_id UUID REFERENCES mission_stops(id) ON DELETE SET NULL,
  dispute_type TEXT NOT NULL,  -- incorrect_location, wrong_cargo, timeout, etc.
  description TEXT,
  photo_url TEXT,
  status TEXT DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'dismissed')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  resolved_at TIMESTAMP WITH TIME ZONE,
  resolved_by_admin_id UUID
);

CREATE INDEX IF NOT EXISTS idx_disputes_mission ON mission_disputes(mission_id);
CREATE INDEX IF NOT EXISTS idx_disputes_driver ON mission_disputes(driver_id);
CREATE INDEX IF NOT EXISTS idx_disputes_status ON mission_disputes(status);

-- ============================================================
-- 8. DRIVER PERFORMANCE METRICS (Computed)
-- ============================================================
CREATE TABLE IF NOT EXISTS driver_performance_daily (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  driver_id UUID NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  deliveries_count INTEGER DEFAULT 0,
  on_time_count INTEGER DEFAULT 0,
  late_count INTEGER DEFAULT 0,
  harsh_braking_count INTEGER DEFAULT 0,
  idling_minutes INTEGER DEFAULT 0,
  fuel_efficiency_liters_per_100km NUMERIC(8,3),
  safety_score NUMERIC(5,2) DEFAULT 0,
  efficiency_score NUMERIC(5,2) DEFAULT 0,
  overall_score NUMERIC(5,2) DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE (driver_id, date)
);

CREATE INDEX IF NOT EXISTS idx_perf_driver ON driver_performance_daily(driver_id);
CREATE INDEX IF NOT EXISTS idx_perf_date ON driver_performance_daily(date DESC);

-- ============================================================
-- 9. BACKWARD COMPATIBILITY: Create views for old schema
-- ============================================================
-- Map old "Truck" concept to new tables
CREATE OR REPLACE VIEW truck_overview AS
SELECT 
  t.id,
  t.truck_identifier AS truck_id,
  t.plate,
  t.status,
  d.display_name AS driver,
  t.last_location_ts AS last_updated,
  t.last_latitude AS lat,
  t.last_longitude AS lng,
  m.id AS current_mission_id,
  m.mission_number AS current_mission,
  m.progress_pct AS progress,
  m.speed_kmh AS speed,
  m.eta,
  t.fuel_consumed_liters,
  t.odometer_km AS distance_travelled,
  t.kilometers_travelled_km AS total_distance
FROM trucks t
LEFT JOIN drivers d ON t.assigned_driver_id = d.id
LEFT JOIN missions m ON t.id = m.truck_id AND m.status IN ('enroute', 'assigned');

-- ============================================================
-- 10. TRIGGERS FOR AUDIT
-- ============================================================
CREATE OR REPLACE FUNCTION log_mission_event()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO mission_events (mission_id, truck_id, driver_id, event_type, payload)
  VALUES (
    COALESCE(NEW.id, OLD.id),
    COALESCE(NEW.truck_id, OLD.truck_id),
    COALESCE(NEW.driver_id, OLD.driver_id),
    TG_ARGV[0],
    jsonb_build_object('before', to_jsonb(OLD), 'after', to_jsonb(NEW))
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mission_status_change
AFTER UPDATE OF status ON missions
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION log_mission_event('status_changed');

-- ============================================================
-- 11. MATERIALIZED VIEWS FOR AGGREGATES
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS driver_aggregate_stats AS
SELECT 
  d.id,
  d.fleet_id,
  d.display_name,
  COUNT(DISTINCT m.id) as total_missions,
  COUNT(DISTINCT CASE WHEN m.status = 'completed' THEN m.id END) as completed_missions,
  SUM(CASE WHEN ms.status = 'completed' THEN 1 ELSE 0 END) as total_deliveries,
  AVG(COALESCE(dpm.overall_score, 0)) as avg_performance_score,
  MAX(dpm.date) as last_performance_date
FROM drivers d
LEFT JOIN missions m ON d.id = m.driver_id
LEFT JOIN mission_stops ms ON m.id = ms.mission_id
LEFT JOIN driver_performance_daily dpm ON d.id = dpm.driver_id
GROUP BY d.id, d.fleet_id, d.display_name;

CREATE INDEX IF NOT EXISTS idx_driver_stats_fleet ON driver_aggregate_stats(fleet_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS truck_aggregate_stats AS
SELECT 
  t.id,
  t.fleet_id,
  t.truck_identifier,
  t.plate,
  COUNT(DISTINCT m.id) as total_missions,
  COUNT(DISTINCT CASE WHEN m.status = 'completed' THEN m.id END) as completed_missions,
  SUM(ms.stop_order) as total_stops_serviced,
  t.fuel_consumed_liters,
  t.odometer_km,
  t.last_location_ts,
  t.status
FROM trucks t
LEFT JOIN missions m ON t.id = m.truck_id
LEFT JOIN mission_stops ms ON m.id = ms.mission_id
WHERE ms.status = 'completed'
GROUP BY t.id, t.fleet_id, t.truck_identifier, t.plate, t.fuel_consumed_liters, 
         t.odometer_km, t.last_location_ts, t.status;

CREATE INDEX IF NOT EXISTS idx_truck_stats_fleet ON truck_aggregate_stats(fleet_id);

-- ============================================================
-- Comment for documentation
-- ============================================================
COMMENT ON TABLE drivers IS 'Driver profiles with performance tracking';
COMMENT ON TABLE trucks IS 'Vehicle assets with telematics';
COMMENT ON TABLE missions IS 'Work items (deliveries/routes)';
COMMENT ON TABLE mission_stops IS 'Normalized delivery stops within missions';
COMMENT ON COLUMN drivers.performance_mark IS 'Computed score 0-100 from daily metrics';
COMMENT ON COLUMN missions.progress_pct IS 'Computed from route polyline and current location';
