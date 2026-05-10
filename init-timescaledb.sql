-- TimescaleDB + PostGIS Initialization Script
-- Creates all tables for Smart Routing System

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis CASCADE;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS fleet;
CREATE SCHEMA IF NOT EXISTS routing;
CREATE SCHEMA IF NOT EXISTS analytics;

SET search_path TO fleet, public;

-- ========================================
-- CORE VEHICLE MANAGEMENT TABLES
-- ========================================

CREATE TABLE IF NOT EXISTS vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fleet_id UUID NOT NULL,
    vehicle_id VARCHAR(50) UNIQUE NOT NULL,
    vehicle_type VARCHAR(20) NOT NULL CHECK (vehicle_type IN ('truck', 'van', 'motorcycle')),
    
    -- Physical properties
    max_weight_kg FLOAT NOT NULL,
    current_load_kg FLOAT DEFAULT 0,
    cargo_type VARCHAR(100),
    max_speed_kmh INT DEFAULT 120,
    
    -- Constraints
    max_daily_hours INT DEFAULT 11,
    current_hours_today INT DEFAULT 0,
    last_break_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Current state
    status VARCHAR(20) DEFAULT 'idle' CHECK (status IN ('idle', 'in_transit', 'at_dock')),
    last_gps_timestamp TIMESTAMP WITH TIME ZONE,
    last_gps_lat FLOAT,
    last_gps_lon FLOAT,
    
    -- Fuel & efficiency
    fuel_type VARCHAR(20),
    fuel_consumption_l_per_100km FLOAT DEFAULT 25.0,
    current_fuel_liters FLOAT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vehicles_fleet_id ON vehicles(fleet_id);
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_vehicle_id ON vehicles(vehicle_id);


-- ========================================
-- GPS TRACKING (HYPERTABLE)
-- ========================================

CREATE TABLE IF NOT EXISTS gps_points (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    lat FLOAT NOT NULL,
    lon FLOAT NOT NULL,
    altitude_m FLOAT,
    speed_kmh FLOAT,
    accuracy_m FLOAT,
    heading_deg FLOAT,
    
    -- Raw vs. snapped state
    snapped BOOLEAN DEFAULT FALSE,
    snapped_lat FLOAT,
    snapped_lon FLOAT,
    road_segment_id BIGINT,
    distance_to_road_m FLOAT,
    
    -- Derived metrics
    acceleration_ms2 FLOAT,
    harsh_braking BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Convert to hypertable
SELECT create_hypertable(
    'gps_points',
    'time',
    if_not_exists => TRUE,
    chunk_time_interval => '1 day'::interval
);

CREATE INDEX idx_gps_vehicle_time ON gps_points (vehicle_id, time DESC);
CREATE INDEX idx_gps_geom ON gps_points USING GIST (ll_to_earth(lat, lon));
CREATE INDEX idx_gps_snapped ON gps_points(snapped);

-- Add compression
ALTER TABLE gps_points SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC'
);
SELECT add_compression_policy('gps_points', INTERVAL '7 days');


-- ========================================
-- TRAIL POLYLINES
-- ========================================

CREATE TABLE IF NOT EXISTS trail_polylines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    
    -- Polyline geometry
    geom GEOMETRY(LineString, 4326) NOT NULL,
    
    -- Metadata
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    point_count INT DEFAULT 0,
    total_distance_km FLOAT,
    total_time_seconds INT,
    
    -- Quality metrics
    map_match_confidence FLOAT DEFAULT 1.0,
    raw_vs_snapped_distance_m FLOAT,
    
    -- Status
    finalized BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trail_vehicle_time ON trail_polylines (vehicle_id, start_time DESC);
CREATE INDEX idx_trail_geom ON trail_polylines USING GIST (geom);
CREATE INDEX idx_trail_finalized ON trail_polylines(finalized);


-- ========================================
-- PLANNED ROUTES
-- ========================================

CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    
    -- Route metadata
    origin_lat FLOAT NOT NULL,
    origin_lon FLOAT NOT NULL,
    destination_lat FLOAT NOT NULL,
    destination_lon FLOAT NOT NULL,
    waypoints JSONB DEFAULT '[]',
    
    -- Route polyline
    planned_polyline GEOMETRY(LineString, 4326),
    planned_distance_km FLOAT,
    planned_duration_seconds INT,
    planned_fuel_liters FLOAT,
    
    -- Constraints
    route_profile VARCHAR(50),
    avoid_hazards BOOLEAN DEFAULT TRUE,
    max_grade_pct FLOAT DEFAULT 15.0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Actual vs planned
    actual_distance_km FLOAT,
    actual_duration_seconds INT,
    actual_fuel_liters FLOAT,
    
    CONSTRAINT route_valid_coords CHECK (
        origin_lat BETWEEN -90 AND 90 AND
        destination_lat BETWEEN -90 AND 90
    )
);

CREATE INDEX idx_routes_vehicle_status ON routes (vehicle_id, status);
CREATE INDEX idx_routes_created_at ON routes (created_at DESC);
CREATE INDEX idx_routes_geom ON routes USING GIST (planned_polyline);


-- ========================================
-- REAL-TIME TRAFFIC EVENTS
-- ========================================

CREATE TABLE IF NOT EXISTS traffic_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event location
    geom GEOMETRY(Point, 4326) NOT NULL,
    lat FLOAT NOT NULL,
    lon FLOAT NOT NULL,
    
    -- Event type
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('accident', 'construction', 'congestion', 'weather')),
    severity VARCHAR(20) DEFAULT 'low' CHECK (severity IN ('low', 'medium', 'high')),
    description TEXT,
    
    -- Impact
    speed_kmh_expected INT,
    delay_minutes INT,
    affected_polyline GEOMETRY(LineString, 4326),
    
    -- Duration
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    estimated_end_time TIMESTAMP WITH TIME ZONE,
    
    -- Source
    source VARCHAR(50),
    confidence FLOAT DEFAULT 0.8,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_traffic_geom ON traffic_events USING GIST (geom);
CREATE INDEX idx_traffic_created_at ON traffic_events (created_at DESC);
CREATE INDEX idx_traffic_event_type ON traffic_events(event_type);


-- ========================================
-- AI-DETECTED HAZARDS
-- ========================================

CREATE TABLE IF NOT EXISTS hazards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Hazard location
    geom GEOMETRY(Point, 4326) NOT NULL,
    lat FLOAT NOT NULL,
    lon FLOAT NOT NULL,
    road_segment_id BIGINT,
    
    -- Classification
    hazard_type VARCHAR(50) NOT NULL CHECK (hazard_type IN (
        'sharp_curve', 'steep_descent', 'sharp_ascent', 'school_zone',
        'railroad_crossing', 'bridge', 'tunnel', 'low_clearance', 'weight_limit'
    )),
    
    severity_score FLOAT DEFAULT 0.5,
    description TEXT,
    
    -- Spatial extent
    affected_polyline GEOMETRY(LineString, 4326),
    recommendation TEXT,
    
    -- OSM metadata
    osm_tags JSONB,
    
    -- Data quality
    confidence FLOAT DEFAULT 0.85,
    source VARCHAR(50) DEFAULT 'ml_inference',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hazards_geom ON hazards USING GIST (geom);
CREATE INDEX idx_hazards_type ON hazards (hazard_type);
CREATE INDEX idx_hazards_confidence ON hazards(confidence);


-- ========================================
-- GEOFENCES & SLA CHECKPOINTS
-- ========================================

CREATE TABLE IF NOT EXISTS geofences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fleet_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    geom GEOMETRY(Polygon, 4326) NOT NULL,
    
    geofence_type VARCHAR(50) CHECK (geofence_type IN ('checkpoint', 'dock', 'exclusion', 'slowzone')),
    
    -- SLA rules (stored as JSONB for flexibility)
    sla_rules JSONB DEFAULT '[]',
    alert_thresholds JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_geofence_geom ON geofences USING GIST (geom);
CREATE INDEX idx_geofence_fleet ON geofences(fleet_id);


-- ========================================
-- SLA BREACH LOG (HYPERTABLE)
-- ========================================

CREATE TABLE IF NOT EXISTS sla_breaches (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    route_id UUID NOT NULL REFERENCES routes(id),
    geofence_id UUID NOT NULL REFERENCES geofences(id),
    
    -- Breach details
    expected_arrival TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_arrival TIMESTAMP WITH TIME ZONE,
    late_by_minutes INT,
    
    -- Impact
    penalty_usd FLOAT,
    customer_notification_sent BOOLEAN DEFAULT FALSE,
    driver_alert_sent BOOLEAN DEFAULT FALSE
);

SELECT create_hypertable(
    'sla_breaches',
    'time',
    if_not_exists => TRUE,
    chunk_time_interval => '1 week'::interval
);

CREATE INDEX idx_sla_vehicle_time ON sla_breaches (vehicle_id, time DESC);
CREATE INDEX idx_sla_route ON sla_breaches(route_id);


-- ========================================
-- ROAD SEGMENTS (STATIC - PostGIS)
-- ========================================

CREATE TABLE IF NOT EXISTS road_segments (
    id BIGINT PRIMARY KEY,
    
    -- Geometry
    geom GEOMETRY(LineString, 4326) NOT NULL,
    length_m FLOAT NOT NULL,
    
    -- Road properties
    osm_way_id BIGINT,
    name VARCHAR(255),
    highway_type VARCHAR(30),
    
    -- Dynamic properties
    speed_limit_kmh INT DEFAULT 50,
    current_avg_speed_kmh INT,
    congestion_level VARCHAR(20) DEFAULT 'unknown',
    
    -- Truck-specific
    truck_allowed BOOLEAN DEFAULT TRUE,
    hazmat_allowed BOOLEAN DEFAULT TRUE,
    weight_limit_tons FLOAT,
    height_limit_m FLOAT,
    
    -- Elevation data
    avg_grade_pct FLOAT,
    max_grade_pct FLOAT,
    elevation_change_m INT,
    
    -- Fuel efficiency
    fuel_efficiency_factor FLOAT DEFAULT 1.0,
    
    -- Hazard flags
    has_sharp_curves BOOLEAN DEFAULT FALSE,
    has_steep_descent BOOLEAN DEFAULT FALSE,
    has_sharp_ascent BOOLEAN DEFAULT FALSE,
    is_school_zone BOOLEAN DEFAULT FALSE,
    has_railroad_crossing BOOLEAN DEFAULT FALSE,
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_road_geom ON road_segments USING GIST (geom);
CREATE INDEX idx_road_highway_type ON road_segments (highway_type);
CREATE INDEX idx_road_name ON road_segments USING GIN (name gin_trgm_ops);


-- ========================================
-- ANALYTICS TABLES (TIMESCALEDB)
-- ========================================

CREATE TABLE IF NOT EXISTS analytics.daily_metrics (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    fleet_id UUID NOT NULL,
    vehicle_id UUID NOT NULL REFERENCES fleet.vehicles(id),
    
    distance_km FLOAT,
    duration_seconds INT,
    fuel_consumed_liters FLOAT,
    fuel_cost_usd FLOAT,
    
    idle_time_seconds INT,
    harsh_brakes INT DEFAULT 0,
    speeding_events INT DEFAULT 0,
    
    sla_breaches INT DEFAULT 0,
    on_time_deliveries INT DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

SELECT create_hypertable(
    'analytics.daily_metrics',
    'time',
    if_not_exists => TRUE,
    chunk_time_interval => '1 day'::interval
);

CREATE INDEX idx_daily_metrics_fleet ON analytics.daily_metrics (fleet_id, time DESC);
CREATE INDEX idx_daily_metrics_vehicle ON analytics.daily_metrics (vehicle_id, time DESC);


-- ========================================
-- VIEWS FOR QUICK QUERIES
-- ========================================

CREATE OR REPLACE VIEW active_routes AS
SELECT 
    r.id,
    r.vehicle_id,
    v.vehicle_id as plate,
    r.origin_lat,
    r.origin_lon,
    r.destination_lat,
    r.destination_lon,
    r.planned_distance_km,
    r.planned_duration_seconds,
    r.status,
    r.created_at
FROM routes r
JOIN vehicles v ON r.vehicle_id = v.id
WHERE r.status IN ('active', 'planned')
ORDER BY r.created_at DESC;


CREATE OR REPLACE VIEW vehicle_latest_positions AS
SELECT DISTINCT ON (vehicle_id)
    vehicle_id,
    lat,
    lon,
    altitude_m,
    speed_kmh,
    heading_deg,
    time,
    accuracy_m
FROM gps_points
ORDER BY vehicle_id, time DESC;


CREATE OR REPLACE VIEW hazard_density_heatmap AS
SELECT
    ST_GeoHash(geom, 6) as geo_hash,
    hazard_type,
    COUNT(*) as count,
    AVG(severity_score) as avg_severity,
    ST_Centroid(ST_Collect(geom)) as center
FROM hazards
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY ST_GeoHash(geom, 6), hazard_type;


-- ========================================
-- SECURITY & RETENTION POLICIES
-- ========================================

-- Enable row-level security (optional)
-- ALTER TABLE gps_points ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE routes ENABLE ROW LEVEL SECURITY;

-- GPS data retention: Keep 30 days, compress after 7 days
SELECT add_retention_policy('gps_points', INTERVAL '30 days', if_not_exists => true);

-- Complete routes retention: Keep 6 months
CREATE OR REPLACE FUNCTION archive_old_routes() RETURNS void AS $$
BEGIN
    DELETE FROM routes
    WHERE completed_at < NOW() - INTERVAL '180 days'
    AND status = 'completed';
END;
$$ LANGUAGE plpgsql;

-- Create job to run daily
SELECT cron.schedule('archive_old_routes', '0 2 * * *', 'SELECT archive_old_routes()');


-- ========================================
-- INITIAL DATA (SAMPLE)
-- ========================================

-- Insert sample fleet
INSERT INTO vehicles (fleet_id, vehicle_id, vehicle_type, max_weight_kg, cargo_type, status)
VALUES (gen_random_uuid(), 'TRUCK-001', 'truck', 20000, 'general', 'idle')
ON CONFLICT (vehicle_id) DO NOTHING;

INSERT INTO vehicles (fleet_id, vehicle_id, vehicle_type, max_weight_kg, cargo_type, status)
VALUES (gen_random_uuid(), 'TRUCK-002', 'truck', 20000, 'perishable', 'idle')
ON CONFLICT (vehicle_id) DO NOTHING;

INSERT INTO vehicles (fleet_id, vehicle_id, vehicle_type, max_weight_kg, cargo_type, status)
VALUES (gen_random_uuid(), 'VAN-001', 'van', 3500, 'general', 'idle')
ON CONFLICT (vehicle_id) DO NOTHING;


GRANT USAGE ON SCHEMA fleet TO fleet_user;
GRANT USAGE ON SCHEMA routing TO fleet_user;
GRANT USAGE ON SCHEMA analytics TO fleet_user;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA fleet TO fleet_user;
GRANT SELECT ON ALL TABLES IN SCHEMA routing TO fleet_user;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA analytics TO fleet_user;


-- Final verification
SELECT 'TimescaleDB + PostGIS initialized successfully' as status;
SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'fleet';
