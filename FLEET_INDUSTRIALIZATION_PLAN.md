# Fleet Management Platform: Industrialization Plan v1.0

**Document Version:** 1.0  
**Last Updated:** May 4, 2026  
**Status:** Ready for Pilot Execution  
**Audience:** Executive Leadership, Engineering, Product, Sales

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Assessment](#current-state-assessment)
3. [MVP Feature Specification](#mvp-feature-specification)
4. [Technical Architecture](#technical-architecture)
5. [Data Model](#data-model)
6. [API Contract & Event Schemas](#api-contract--event-schemas)
7. [Mobile Driver App Specification](#mobile-driver-app-specification)
8. [Production Deployment Architecture](#production-deployment-architecture)
9. [Prioritized Feature Backlog](#prioritized-feature-backlog)
10. [Testing & QA Strategy](#testing--qa-strategy)
11. [Security & Compliance Framework](#security--compliance-framework)
12. [Observability & Monitoring](#observability--monitoring)
13. [Migration & Pilot Strategy](#migration--pilot-strategy)
14. [12-Week Execution Roadmap](#12-week-execution-roadmap)
15. [KPIs & Success Metrics](#kpis--success-metrics)
16. [Pricing & Commercial Model](#pricing--commercial-model)
17. [Sales One-Pager](#sales-one-pager)

---

## Executive Summary

**Industrialization Objective:** Transform the existing fleet management web app into a production-grade, multi-tenant SaaS platform supporting 10–10,000 vehicles with real-time GPS tracking, predictive maintenance, driver scoring, and compliance automation.

### Key Strategic Initiatives

1. **Fix Reliability First** (Weeks 1–2)
   - Eliminate map rendering bugs and telemetry gaps
   - Add deterministic replay for debugging
   - Establish automated alerting for data loss

2. **MVP Launch** (Weeks 3–8)
   - Web admin dashboard with live map, vehicle list, and trip replay
   - Native mobile driver app (iOS/Android) with background GPS tracking
   - Driver scoring with dispute workflow
   - REST + WebSocket APIs for real-time updates
   - Role-based access control and OAuth2 SSO

3. **Pilot & Validation** (Weeks 7–12)
   - Onboard 3 pilot customers (10–50 vehicles each)
   - Production readiness testing (99.9% uptime, <2s map updates)
   - Security audit and compliance certification
   - Collect ROI metrics (fuel savings, time optimization, maintenance alerts)

4. **v1 Scale & Features** (Weeks 9–20)
   - Predictive maintenance module with ML scoring
   - ROI dashboard with cost savings projections
   - Multi-tenant billing and usage metering
   - Compliance module (HOS logs, geofence automation)

5. **Long-Term Differentiation** (v2, Weeks 21–36)
   - Advanced ML for ETA and fuel optimization
   - Marketplace integrations (fuel cards, maintenance partners)
   - White-labeling and enterprise SSO federation
   - Offline map tiles and advanced caching

**Success Metrics (Pilot Phase):**
- Ingestion uptime ≥ 99.9%
- Map update latency <2s (p95)
- Pilot conversion rate to paid ≥ 40%
- Customer onboarding time ≤ 2 hours

---

## Current State Assessment

### Existing Codebase Review

**Frontend (React 19.2.5 + Vite 5.4.21)**
- Real-time vehicle tracking UI with Leaflet maps
- RoadMatchedTrailSystem component rendering GPS trails
- DriverEventAlerts system (recently refactored for consolidation)
- Alert deduplication via AlertManager service
- Responsive design with TailwindCSS

**Backend (Django 6.0.4 + SQLite)**
- Vehicle tracking REST API
- GPS location ingestion endpoints
- Basic alert management
- SQLite database (not production-scale)

**Issues to Address**
1. ⚠️ **Single-tenant SQLite database** → migrate to PostgreSQL with multi-tenant schema
2. ⚠️ **No real-time WebSocket layer** → add WebSocket service for <500ms event latency
3. ⚠️ **GPS data not time-series optimized** → migrate to TimescaleDB or ClickHouse
4. ⚠️ **No horizontal scaling** → containerize, add Kubernetes orchestration
5. ⚠️ **Alert spam on high event volume** → already addressed with AlertManager, now need production validation
6. ⚠️ **No audit logging or compliance** → add immutable audit trail, GDPR data export/deletion
7. ⚠️ **No mobile app** → design and build native driver app from scratch

---

## MVP Feature Specification

### Core Capabilities (Weeks 0–8)

#### 1. Real-Time GPS Ingestion & Device Tracking

**Feature:**
- Vehicles send GPS updates at adaptive intervals (1–5s while driving, 30–300s while idle)
- Mobile app uses platform location APIs (iOS Significant Location Change, Android Foreground Service)
- Server accepts both mobile and external tracker (Samsara, Verizon Connect) feeds

**Acceptance Criteria:**
- ✓ Accept ≥10k location events/sec without data loss
- ✓ Store location with ±5m accuracy metadata
- ✓ Device heartbeat timeout detection (alert if no update for 5 min)
- ✓ Support multi-source tracking (mobile, GPS device, OBD-II)

**API Endpoint:**
```http
POST /api/v1/vehicles/{vehicleId}/locations

{
  "timestamp": "2026-05-04T22:58:00Z",
  "latitude": -18.9707,
  "longitude": 32.6700,
  "speed_kmh": 52.3,
  "heading_degrees": 180,
  "accuracy_meters": 8,
  "battery_percent": 0.72,
  "source": "mobile|tracker|obd",
  "device_id": "device_abc123"
}

Response: 202 Accepted
{
  "id": "loc_event_xyz789",
  "ingested_at": "2026-05-04T22:58:01Z"
}
```

#### 2. Reliable Map Rendering & Trip Playback

**Feature:**
- Live map showing all vehicles in real time
- Trip playback with scrubber control (rewind/forward, speed control)
- Server-side route caching to reduce frontend rendering work
- Deterministic replay mode for debugging

**Acceptance Criteria:**
- ✓ Map renders 1000+ vehicles without frame drops (<60 FPS)
- ✓ Trip playback supports 1–4x speed, pause/resume
- ✓ Route cache hit rate >80%
- ✓ Deterministic replay matches live logs exactly
- ✓ <500ms time to first map render

**Implementation Notes:**
- Use Leaflet vector layers with clustering for performance
- Server caches route polylines in Redis (TTL 7 days)
- Implement trip playback API that returns time-indexed location arrays

#### 3. Native Mobile Driver App

**Feature:**
- Background GPS tracking while app is closed
- Offline event queue with eventual sync
- Low-battery mode with reduced sampling
- Permission flows with user rationale screens
- Shift start/end tracking
- Dispute workflow (driver can flag trips with notes/photos)

**Acceptance Criteria:**
- ✓ Background GPS works for ≥8 hours on 4000 mAh battery
- ✓ Offline queue survives app crash
- ✓ Battery drain <5% per hour in balanced mode
- ✓ Photo upload <5MB per trip
- ✓ All tracking stops when driver pauses (privacy controls)

**Platform Support:**
- Android 12+ (API 31+)
- iOS 16+ (iOS 16, 17, 18)
- Distribution: Play Store, App Store, enterprise APK/IPA

#### 4. Admin Dashboard: Live Fleet View

**Feature:**
- Single map view showing all vehicles
- Vehicle list with live status (online, idle, offline, geofence breach)
- Quick-filter by status, driver, region, geofence
- Drill-down into vehicle detail (trip history, driver, maintenance)
- KPI summary cards (vehicles online, avg speed, fuel burn, maintenance due)

**Acceptance Criteria:**
- ✓ Dashboard loads in <3s
- ✓ Map updates every 2–5s for all vehicles
- ✓ Filter and search complete in <200ms
- ✓ KPI cards refresh every 30s
- ✓ Support concurrent users without performance degradation

#### 5. Driver Scoring & Dispute Workflow

**Feature:**
- Real-time scoring for harsh braking, overspeeding, idling, harsh acceleration
- Trip score calculation (0–100 scale)
- Driver view: see their own score and recent incidents
- Dispute flow: driver flags a trip segment with notes/photos
- Admin review: approve or reject dispute, adjust score

**Scoring Formula:**
```
Trip Score = 100
- (harsh_brake_count × 3)
- (speed_violation_count × 2)
- (idle_time_minutes / 10)
- (harsh_accel_count × 2)

Harsh Brake: deceleration > 6 m/s²
Overspeed: >5 km/h above posted limit for >10s
Idle: engine on, speed <1 km/h for >2 min
Harsh Accel: acceleration > 5 m/s²
```

**Acceptance Criteria:**
- ✓ Score calculated within 5s of trip completion
- ✓ Driver dispute recorded with timestamp and photo (if provided)
- ✓ Admin dispute review shows before/after score
- ✓ Scorecard available in driver app and admin dashboard
- ✓ Historical scores visible for 12 months

#### 6. REST API & WebSocket Real-Time Layer

**Feature:**
- RESTful API for queries, mutations, data export
- WebSocket endpoint for real-time vehicle updates and alerts
- OAuth2 SSO for web; OAuth2 PKCE for mobile
- Rate limiting (1000 req/min per tenant)
- Automatic token refresh

**Acceptance Criteria:**
- ✓ All endpoints authenticated with OAuth2
- ✓ WebSocket latency <500ms (median), <2s (p95)
- ✓ Token TTL 1 hour; refresh token TTL 30 days
- ✓ Rate limit returns 429 with retry-after header
- ✓ API versioning supports v1, v2 without breaking clients

#### 7. Security: OAuth2 SSO, RBAC, Audit Logging

**Feature:**
- OAuth2 login with enterprise SSO support (Okta, Azure AD)
- Role-based access control (admin, manager, driver, viewer)
- TLS 1.3 for all transport
- AES-256 encryption at rest for sensitive data (PII, photos)
- Immutable audit log for admin actions
- Quarterly penetration testing

**Roles:**
- **Admin:** Full access, billing, user management, audit logs
- **Manager:** Fleet view, driver management, dispute review
- **Driver:** Own trip history, scoring, dispute filing
- **Viewer:** Read-only dashboard (e.g., finance team)

**Acceptance Criteria:**
- ✓ All admin actions logged (create/edit/delete)
- ✓ Audit log immutable (append-only, cryptographically signed)
- ✓ Data export and deletion endpoints available (GDPR)
- ✓ No plaintext PII in logs
- ✓ Pen test findings resolved before production

#### 8. Pilot Program & Onboarding

**Feature:**
- 30–90 day pilot template with defined success metrics
- Pilot onboarding checklist (device setup, user training, test scenarios)
- Dedicated pilot support channel
- Weekly check-ins and ROI tracking
- Automated pilot offer (discounted rate, free onboarding, success guarantee)

**Acceptance Criteria:**
- ✓ Pilot checklist covers all major features
- ✓ Onboarding time ≤ 2 hours per vehicle
- ✓ Pilot ROI dashboard shows fuel, time, and maintenance savings
- ✓ Target 40%+ conversion to paid contract

---

## Technical Architecture

### High-Level System Design

```
┌────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├──────────────────────┬──────────────────────┬──────────────────┤
│  Web Admin Dashboard │  Mobile Driver App   │  Third-party API │
│  (React + Leaflet)   │  (React Native/      │  (Partner         │
│                      │   Flutter)           │   Integrations)   │
└──────────┬───────────┴──────────┬───────────┴──────────┬────────┘
           │                      │                      │
           │  REST + WebSocket    │  REST + WebSocket    │  REST
           │  (OAuth2)            │  (PKCE)              │  (API Key)
           │                      │                      │
┌──────────▼──────────────────────▼──────────────────────▼────────┐
│                  API GATEWAY & LOAD BALANCER                      │
│              (Nginx + ModSecurity WAF rules)                      │
└──────────┬──────────────────────────────────────────────────────┘
           │
      ┌────▼────────────────────────────────────────┐
      │     KUBERNETES ORCHESTRATION (3 zones)      │
      └────┬────────────────────────────────────────┘
           │
    ┌──────┴──────────────────────────────┬──────────────┐
    │                                      │              │
┌───▼───────────────────┐  ┌─────────────▼──────┐  ┌─────▼─────────┐
│  INGESTION SERVICE    │  │  API SERVICE       │  │ WEBSOCKET SVC │
│  (Autoscale 5–50x)    │  │  (Autoscale 2–20x) │  │  (Autoscale    │
│                       │  │                    │  │   2–10x)      │
│ • POST /locations     │  │  • GET /vehicles   │  │               │
│ • Batch decode        │  │  • POST /alerts    │  │ • WebSocket   │
│ • Validate accuracy   │  │  • PUT /trips      │  │   broker      │
│ • Enrich location     │  │                    │  │ • Redis pub   │
│ • Route to Kafka      │  │                    │  │   /sub        │
└───┬─────────────────┬─┘  └─────────────────┬──┘  └────┬─────────┘
    │                 │                      │           │
    └────┬────────────┴──────────────────────┴───────────┘
         │
    ┌────▼─────────────────────────────────┐
    │   KAFKA EVENT BUS (multi-partition)   │
    │                                       │
    │ • vehicle.location                    │
    │ • vehicle.status                      │
    │ • trip.created / trip.completed       │
    │ • alert.created / alert.resolved      │
    │ • driver.scored                       │
    └────┬────────────────────────────────┬┘
         │                                │
    ┌────▼──────────────┐  ┌─────────────▼─────────┐
    │ PROCESSING LAYER  │  │  ASYNC JOBS           │
    ├───────────────────┤  ├───────────────────────┤
    │ • Smoothing       │  │ • Trip scoring (Spark)│
    │ • Geofence check  │  │ • Predictive maint.   │
    │ • Scoring engine  │  │ • Route optimization  │
    │ • Alert trigger   │  │ • ML model updates    │
    │ • Cache refresh   │  │ • Data export/GDPR    │
    └────┬──────────────┘  └───────────┬───────────┘
         │                             │
    ┌────▼─────────────────────────────▼──────────────┐
    │         STORAGE & CACHING LAYER                 │
    ├─────────────────────────────────────────────────┤
    │ • PostgreSQL (fleet, users, audit logs, config) │
    │ • TimescaleDB (location telemetry hot tier)     │
    │ • ClickHouse (analytics queries, cold tier)     │
    │ • Redis (cache, sessions, rate limit counters)  │
    │ • S3 (trip photos, exports, backups)            │
    │ • Elasticsearch (audit logs, search)            │
    └─────────────────────────────────────────────────┘
    
    │
    ├─ Monitoring & Observability ─────────────────┐
    │ • Prometheus (metrics)                       │
    │ • Jaeger (distributed traces)                │
    │ • ELK Stack (logs)                           │
    │ • Grafana (dashboards & SLOs)                │
    │ • PagerDuty (on-call alerting)               │
    └────────────────────────────────────────────┘
```

### Scaling Strategy

**Horizontal Scaling:**
- Ingestion service: 1 pod/200 vehicles; scale to 50 under load
- API service: 1 pod/500 concurrent users; scale to 20
- WebSocket: 1 pod/5000 concurrent connections; scale to 10
- Kafka consumers: 1 worker/partition; scale with topic growth

**Vertical Optimization:**
- Use CPU-optimized nodes for API services
- Use memory-optimized nodes for Redis, cache layer
- Use ARM64 nodes (Graviton) for batch jobs (cost ↓30%)

**Data Partitioning:**
- Partition Kafka topics by `fleet_id` mod 64
- Partition TimescaleDB by `(fleet_id, day)`
- Partition ClickHouse by `(fleet_id, week)`
- Query router directs traffic to correct shard

**Cost Control:**
- Use spot instances (70% cheaper) for batch ML, reporting
- Reserved capacity for ingestion and API services
- Auto-scale down to 0 pods during off-peak (e.g., 10 PM–6 AM)
- Monitor cost per vehicle ingested; alert on >$0.50/vehicle/month

---

## Data Model

### Core Schema (PostgreSQL)

```sql
-- Multi-tenant foundation
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  billing_plan VARCHAR(50), -- 'smb_starter', 'smb_pro', 'enterprise'
  billing_contact_email VARCHAR(255),
  data_retention_days INT DEFAULT 365,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(name)
);

-- Fleets (customer's logical grouping of vehicles)
CREATE TABLE fleets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  region VARCHAR(50), -- 'ZA', 'KE', 'NG', etc.
  timezone VARCHAR(50) DEFAULT 'UTC',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(org_id, name),
  INDEX idx_org_id (org_id)
);

-- Vehicles
CREATE TABLE vehicles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fleet_id UUID NOT NULL REFERENCES fleets(id) ON DELETE CASCADE,
  external_id VARCHAR(255), -- 'TRUCK-001', 'VAN-42'
  vin VARCHAR(17) UNIQUE,
  make VARCHAR(100),
  model VARCHAR(100),
  year INT,
  license_plate VARCHAR(20),
  current_driver_id UUID,
  tracker_id VARCHAR(255), -- external GPS device ID
  tracker_type VARCHAR(50), -- 'samsara', 'verizon', 'mobile', 'obd'
  status VARCHAR(50) DEFAULT 'offline', -- 'online', 'idle', 'offline', 'maintenance'
  last_location_lat FLOAT,
  last_location_lon FLOAT,
  last_location_ts TIMESTAMP,
  battery_percent FLOAT,
  odometer_km FLOAT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_fleet_id (fleet_id),
  INDEX idx_status (status)
);

-- Drivers
CREATE TABLE drivers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fleet_id UUID NOT NULL REFERENCES fleets(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  phone_hash VARCHAR(64), -- hashed for privacy
  license_number_hash VARCHAR(64),
  license_expiry_date DATE,
  opt_in_scoring BOOLEAN DEFAULT FALSE,
  opt_in_mobile_tracking BOOLEAN DEFAULT FALSE,
  status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'suspended'
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_fleet_id (fleet_id)
);

-- Trips (completed or in-progress journeys)
CREATE TABLE trips (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
  driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
  fleet_id UUID NOT NULL REFERENCES fleets(id) ON DELETE CASCADE,
  start_ts TIMESTAMP NOT NULL,
  end_ts TIMESTAMP,
  start_lat FLOAT,
  start_lon FLOAT,
  end_lat FLOAT,
  end_lon FLOAT,
  distance_km FLOAT,
  duration_seconds INT,
  score INT, -- 0-100
  harsh_brakes INT DEFAULT 0,
  overspeeds INT DEFAULT 0,
  harsh_accelerations INT DEFAULT 0,
  idle_time_minutes INT DEFAULT 0,
  route_id VARCHAR(255), -- reference to cached route
  completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_vehicle_id (vehicle_id),
  INDEX idx_driver_id (driver_id),
  INDEX idx_fleet_id (fleet_id),
  INDEX idx_start_ts (start_ts),
  INDEX idx_completed (completed)
);

-- Alerts (violations, geofence breaches, maintenance)
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fleet_id UUID NOT NULL REFERENCES fleets(id) ON DELETE CASCADE,
  vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
  driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
  alert_type VARCHAR(50) NOT NULL, -- 'off_route', 'overspeed', 'geofence_breach', 'maintenance_due', 'harsh_braking'
  severity VARCHAR(50) DEFAULT 'info', -- 'critical', 'warning', 'info'
  message TEXT,
  details JSONB, -- flexible for extensibility
  is_resolved BOOLEAN DEFAULT FALSE,
  resolved_at TIMESTAMP,
  resolved_by_user_id UUID,
  resolution_note TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_fleet_id (fleet_id),
  INDEX idx_vehicle_id (vehicle_id),
  INDEX idx_is_resolved (is_resolved),
  INDEX idx_created_at (created_at)
);

-- Geofences (service areas, zones, restricted areas)
CREATE TABLE geofences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fleet_id UUID NOT NULL REFERENCES fleets(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  boundary_geom GEOMETRY(Polygon, 4326), -- PostGIS
  trigger_type VARCHAR(50), -- 'entry', 'exit', 'dwell'
  dwell_time_minutes INT,
  action_type VARCHAR(50), -- 'alert', 'log'
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_fleet_id (fleet_id),
  SPATIAL INDEX idx_boundary (boundary_geom)
);

-- Audit log (immutable)
CREATE TABLE audit_logs (
  id BIGSERIAL PRIMARY KEY,
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID,
  resource_type VARCHAR(100), -- 'vehicle', 'driver', 'geofence', 'user'
  resource_id UUID,
  action VARCHAR(50), -- 'create', 'update', 'delete', 'export'
  old_values JSONB,
  new_values JSONB,
  ip_address INET,
  user_agent VARCHAR(512),
  timestamp TIMESTAMP DEFAULT NOW(),
  INDEX idx_org_id (org_id),
  INDEX idx_timestamp (timestamp)
);

-- API keys (for partner integrations)
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  key_hash VARCHAR(64) NOT NULL UNIQUE,
  name VARCHAR(255),
  scopes JSONB, -- ['vehicles:read', 'locations:write']
  last_used_at TIMESTAMP,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_org_id (org_id)
);

-- Users & Access Control
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  role VARCHAR(50) NOT NULL DEFAULT 'viewer', -- 'admin', 'manager', 'driver', 'viewer'
  sso_provider VARCHAR(50), -- 'okta', 'azure_ad', 'google'
  sso_id VARCHAR(255),
  last_login_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(org_id, email),
  INDEX idx_org_id (org_id),
  INDEX idx_sso_id (sso_provider, sso_id)
);
```

### Time-Series Schema (TimescaleDB for hot location data)

```sql
-- Locations: high-volume, time-series optimized
CREATE TABLE locations (
  time TIMESTAMP NOT NULL,
  vehicle_id UUID NOT NULL,
  fleet_id UUID NOT NULL,
  latitude FLOAT NOT NULL,
  longitude FLOAT NOT NULL,
  speed_kmh FLOAT,
  heading_degrees INT,
  accuracy_meters INT,
  battery_percent FLOAT,
  source VARCHAR(50), -- 'mobile', 'tracker', 'obd'
  device_id VARCHAR(255)
);

-- Hypertable for automatic partitioning by time
SELECT create_hypertable('locations', 'time', 
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE);

-- Compression after 30 days
ALTER TABLE locations SET (
  timescaledb.compress,
  timescaledb.compress_orderby = 'time DESC',
  timescaledb.compress_segmentby = 'fleet_id,vehicle_id'
);

SELECT add_compression_policy('locations',
  COMPRESS_AFTER => INTERVAL '30 days');

-- Indexes for typical queries
CREATE INDEX idx_locations_fleet_time 
  ON locations (fleet_id, time DESC);

CREATE INDEX idx_locations_vehicle_time 
  ON locations (vehicle_id, time DESC);
```

### Analytics Schema (ClickHouse for cold data & aggregations)

```sql
-- Use ClickHouse for cost-effective analytics on historical data
-- Data flows: TimescaleDB → Kafka → ClickHouse (daily batch)

CREATE TABLE locations_analytics (
  time DateTime,
  fleet_id UUID,
  vehicle_id UUID,
  latitude Float32,
  longitude Float32,
  speed_kmh Float32,
  accuracy_meters Int32,
  source String
) ENGINE = MergeTree()
ORDER BY (fleet_id, time)
PARTITION BY toYYYYMM(time)
TTL time + INTERVAL 12 MONTH;

-- Pre-aggregated trip summary for fast dashboards
CREATE TABLE trip_stats (
  date Date,
  fleet_id UUID,
  vehicle_id UUID,
  trips_count UInt32,
  total_distance_km Float32,
  avg_speed_kmh Float32,
  harsh_brakes_count UInt32,
  overspeed_violations UInt32,
  avg_trip_score Int32
) ENGINE = SummingMergeTree()
ORDER BY (fleet_id, date)
PARTITION BY toYYYYMM(date);
```

### Event Streaming Schema (Kafka Topics)

```json
// Topic: vehicle.location
// Partition key: fleet_id
// Retention: 7 days (hot, for replay)
{
  "eventId": "loc_evt_abc123",
  "eventType": "vehicle.location",
  "timestamp": "2026-05-04T22:58:00.123Z",
  "version": "1.0",
  "fleetId": "fleet_xyz",
  "vehicleId": "veh_123",
  "latitude": -18.9707,
  "longitude": 32.6700,
  "speedKmh": 52.3,
  "headingDegrees": 180,
  "accuracyMeters": 8,
  "batteryPercent": 0.72,
  "source": "mobile|tracker|obd",
  "deviceId": "device_abc123"
}

// Topic: vehicle.status
// Partition key: fleet_id
// Retention: 30 days
{
  "eventId": "status_evt_def456",
  "eventType": "vehicle.status",
  "timestamp": "2026-05-04T22:58:00.123Z",
  "fleetId": "fleet_xyz",
  "vehicleId": "veh_123",
  "status": "online|idle|offline|maintenance",
  "reason": "heartbeat|manual|timeout",
  "previousStatus": "online"
}

// Topic: alert.created
// Partition key: fleet_id
// Retention: 90 days
{
  "eventId": "alert_evt_ghi789",
  "eventType": "alert.created",
  "timestamp": "2026-05-04T22:58:00.123Z",
  "fleetId": "fleet_xyz",
  "vehicleId": "veh_123",
  "driverId": "driver_456",
  "alertType": "off_route|overspeed|geofence_breach|maintenance_due",
  "severity": "critical|warning|info",
  "message": "Vehicle off-route by 500m",
  "details": {
    "expectedLat": -18.970,
    "expectedLon": 32.670,
    "actualLat": -18.975,
    "actualLon": 32.665,
    "deviationMeters": 500
  }
}

// Topic: trip.completed
// Partition key: fleet_id
// Retention: 365 days
{
  "eventId": "trip_evt_jkl012",
  "eventType": "trip.completed",
  "timestamp": "2026-05-04T22:58:00.123Z",
  "fleetId": "fleet_xyz",
  "tripId": "trip_789",
  "vehicleId": "veh_123",
  "driverId": "driver_456",
  "startTime": "2026-05-04T20:00:00Z",
  "endTime": "2026-05-04T22:58:00Z",
  "distanceKm": 125.5,
  "score": 85,
  "harshBrakes": 2,
  "overspeeds": 1,
  "harshAccelerations": 0,
  "idleTimeMinutes": 15,
  "fuelEstimatedLiters": 8.5
}
```

---

## API Contract & Event Schemas

### Authentication

**OAuth2 Token Exchange (Server-to-Server)**
```http
POST /auth/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=org_abc123_backend
&client_secret=secret_xyz789
&scope=vehicles:read locations:write alerts:read

Response: 200 OK
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "vehicles:read locations:write alerts:read"
}
```

**OAuth2 PKCE Flow (Mobile)**
```http
POST /auth/oauth/authorize?
  client_id=com.fleet.driver.mobile
  &redirect_uri=com.fleet.driver://oauth-callback
  &response_type=code
  &scope=locations:write trips:read
  &state=random_state_xyz
  &code_challenge=challenge_hash
  &code_challenge_method=S256

// After user login and consent → authorization code
POST /auth/oauth/token
{
  "grant_type": "authorization_code",
  "code": "auth_code_abc123",
  "client_id": "com.fleet.driver.mobile",
  "redirect_uri": "com.fleet.driver://oauth-callback",
  "code_verifier": "verifier_xyz"
}
```

### REST API Endpoints

#### Vehicle Management

```http
GET /api/v1/fleets/{fleetId}/vehicles
Query params:
  - status: online|idle|offline|maintenance
  - limit: 100
  - offset: 0
  - sort_by: name|status|last_update

Response: 200 OK
{
  "data": [
    {
      "id": "veh_123",
      "externalId": "TRUCK-001",
      "vin": "1HGBH41JXMN109186",
      "make": "Hino",
      "model": "500",
      "licenseplate": "ABC-123",
      "status": "online",
      "currentDriverId": "driver_456",
      "lastLocation": {
        "latitude": -18.9707,
        "longitude": 32.6700,
        "timestamp": "2026-05-04T22:58:00Z",
        "speedKmh": 52.3,
        "accuracyMeters": 8
      },
      "batteryPercent": 0.72,
      "odometerKm": 125000.5
    }
  ],
  "total": 47,
  "hasMore": false
}
```

#### Location Ingestion

```http
POST /api/v1/vehicles/{vehicleId}/locations
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "timestamp": "2026-05-04T22:58:00.123Z",
  "latitude": -18.9707,
  "longitude": 32.6700,
  "speedKmh": 52.3,
  "headingDegrees": 180,
  "accuracyMeters": 8,
  "batteryPercent": 0.72,
  "source": "mobile",
  "deviceId": "device_abc123",
  "tripId": "trip_789"  // optional: associate with trip
}

Response: 202 Accepted
{
  "id": "loc_evt_abc123",
  "ingestedAt": "2026-05-04T22:58:01Z",
  "status": "queued_for_processing"
}
```

**Batch Ingestion (for efficiency)**
```http
POST /api/v1/vehicles/{vehicleId}/locations/batch
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "locations": [
    {
      "timestamp": "2026-05-04T22:55:00Z",
      "latitude": -18.970,
      "longitude": 32.669,
      "speedKmh": 50.0
    },
    {
      "timestamp": "2026-05-04T22:56:00Z",
      "latitude": -18.9707,
      "longitude": 32.6700,
      "speedKmh": 52.3
    }
  ]
}

Response: 202 Accepted
{
  "batchId": "batch_xyz789",
  "itemsQueued": 2,
  "itemsFailed": 0
}
```

#### Alert Management

```http
GET /api/v1/fleets/{fleetId}/alerts
Query params:
  - isResolved: false
  - severity: critical|warning|info
  - alertType: off_route|overspeed|...
  - limit: 50

Response: 200 OK
{
  "data": [
    {
      "id": "alert_xyz",
      "vehicleId": "veh_123",
      "driverId": "driver_456",
      "alertType": "off_route_detected",
      "severity": "critical",
      "message": "Vehicle off-route by 500m",
      "isResolved": false,
      "createdAt": "2026-05-04T22:58:00Z",
      "details": {
        "expectedLat": -18.970,
        "actualLat": -18.975,
        "deviationMeters": 500
      }
    }
  ]
}

POST /api/v1/alerts/{alertId}/resolve
{
  "note": "False positive, construction zone",
  "approveDispute": true
}

Response: 200 OK
{
  "id": "alert_xyz",
  "resolvedAt": "2026-05-04T23:00:00Z",
  "isResolved": true
}
```

#### Trip Playback

```http
GET /api/v1/trips/{tripId}/locations
Query params:
  - timeStart: ISO8601
  - timeEnd: ISO8601
  - resample: 1s|5s|10s (default: as recorded)

Response: 200 OK
{
  "tripId": "trip_789",
  "startTime": "2026-05-04T20:00:00Z",
  "endTime": "2026-05-04T22:58:00Z",
  "locations": [
    {
      "timestamp": "2026-05-04T20:00:00Z",
      "latitude": -18.9707,
      "longitude": 32.6700,
      "speedKmh": 0,
      "heading": 0
    },
    // ... more points
  ],
  "polyline": "encoded_polyline_string_for_leaflet"
}
```

#### Driver Scoring & Disputes

```http
GET /api/v1/drivers/{driverId}/score
Response: 200 OK
{
  "driverId": "driver_456",
  "periodStartDate": "2026-05-01",
  "periodEndDate": "2026-05-31",
  "averageScore": 82,
  "tripsCompleted": 24,
  "harshBrakes": 8,
  "overspeeds": 12,
  "harshAccelerations": 3,
  "totalIdleTime": 180,
  "safetyRank": "7th / 48 drivers"
}

POST /api/v1/trips/{tripId}/dispute
{
  "reason": "GPS error during road construction",
  "notes": "Construction blocking expected route",
  "photoUrl": "s3://bucket/dispute_photo_xyz.jpg"
}

Response: 201 Created
{
  "disputeId": "dispute_abc123",
  "tripId": "trip_789",
  "status": "pending_review",
  "createdAt": "2026-05-04T23:00:00Z"
}
```

### WebSocket Real-Time Events

**Connection & Subscribe**
```javascript
// Client connects
const socket = new WebSocket('wss://api.example.com/realtime?token=eyJhbGc...');

socket.onopen = () => {
  // Subscribe to fleet updates
  socket.send(JSON.stringify({
    action: 'subscribe',
    channels: ['fleet:fleet_xyz', 'vehicle:veh_123']
  }));
};

socket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // Handle real-time update
  console.log(message);
};
```

**Event: Vehicle Location Update**
```json
{
  "type": "vehicle.location",
  "channel": "vehicle:veh_123",
  "data": {
    "vehicleId": "veh_123",
    "latitude": -18.9707,
    "longitude": 32.6700,
    "speedKmh": 52.3,
    "heading": 180,
    "timestamp": "2026-05-04T22:58:01.234Z",
    "battery": 0.72
  }
}
```

**Event: Alert Created**
```json
{
  "type": "alert.created",
  "channel": "fleet:fleet_xyz",
  "data": {
    "id": "alert_xyz",
    "vehicleId": "veh_123",
    "alertType": "overspeed",
    "severity": "warning",
    "message": "Speed 85 km/h in 60 km/h zone",
    "createdAt": "2026-05-04T22:58:00Z"
  }
}
```

**Event: Vehicle Status Change**
```json
{
  "type": "vehicle.status",
  "channel": "vehicle:veh_123",
  "data": {
    "vehicleId": "veh_123",
    "status": "offline",
    "reason": "timeout",
    "lastHeartbeat": "2026-05-04T22:50:00Z",
    "timestamp": "2026-05-04T22:58:00Z"
  }
}
```

---

## Mobile Driver App Specification

### Platform & Technology Stack

**Framework Choice:**
- **Recommended: React Native** (team expertise with React, faster MVP, code sharing with web admin)
- Alternative: Flutter (if native Android/iOS performance is critical)

**Minimum Requirements:**
- Android 12+ (API 31+)
- iOS 16+ (iOS 16, 17, 18)

**Core Libraries:**
```json
{
  "react-native": "^0.73",
  "react-navigation": "^6.x",
  "@react-native-async-storage/async-storage": "^1.x",
  "@react-native-community/geolocation": "^3.x",
  "react-native-maps": "^1.x",
  "react-native-camera": "^4.x",
  "redux": "^4.x",
  "redux-persist": "^6.x",
  "expo": "^50.x",
  "@sentry/react-native": "^5.x"
}
```

### Wireflow: Core User Journeys

#### 1. Onboarding Flow

```
┌────────────────────────────────────┐
│ Splash / App Load                  │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ SSO / Token Login Screen           │
│ • QR code scan or manual token     │
│ • "Continue with Okta/Azure"       │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ Privacy & Location Permissions     │
│ • "Fleet needs background location"│
│ • Consent to scoring & trip record │
│ • Pause tracking (personal time)   │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ Request Location Permission        │
│ iOS: "Allow Always" / Android:     │
│ "Allow all the time"               │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ Dashboard: Shift Ready             │
│ • Start Shift button (prominent)   │
│ • Device health check (GPS, battery│
│ • Recent trips & score             │
└────────────────────────────────────┘
```

#### 2. Shift Start / End Flow

```
┌────────────────────────────────────┐
│ Tap "Start Shift"                  │
└───────────────┬────────────────────┘
                │
                ▼ Request high-accuracy location 30s
┌────────────────────────────────────┐
│ GPS Calibration (30s spinner)      │
│ "Getting precise location..."      │
└───────────────┬────────────────────┘
                │
                ▼ Switch to balanced mode after 30s
┌────────────────────────────────────┐
│ Shift Active Screen                │
│ • Real-time map (map tile)         │
│ • Current trip duration            │
│ • Distance traveled                │
│ • Speed                            │
│ • Pause Tracking / End Shift       │
└────────────────────────────────────┘
                │
      ┌─────────┴─────────┐
      │                   │
      ▼ (after 8+ hours)  ▼ (driver taps)
┌──────────────────┐  ┌──────────────────┐
│ Auto-end (alert)│  │ End Shift        │
│ Battery low,    │  │ Confirm end &    │
│ connectivity    │  │ save trip        │
└────────────────┘  └──────────────────┘
```

#### 3. Trip Dispute Flow

```
┌────────────────────────────────────┐
│ Trip History / Scorecard            │
│ • List of recent trips             │
│ • Trip score: 85/100               │
│ • Tap trip row for detail          │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ Trip Detail                        │
│ • Map replay (play/pause)          │
│ • Incidents: 1 harsh brake, 2 speeds
│ • "Dispute This Trip" button       │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ File Dispute                       │
│ • Reason dropdown                  │
│ • Notes text area                  │
│ • Attach photo / voice note        │
│ • Submit & confirm                 │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ Dispute Submitted                  │
│ • Status: "Awaiting Admin Review"  │
│ • Est. decision time: 48 hours     │
│ • Will be notified when resolved   │
└────────────────────────────────────┘
```

### Background GPS Strategy

**iOS Implementation (Significant Location Changes + Timer)**

```swift
import CoreLocation

class BackgroundGPSManager: NSObject, CLLocationManagerDelegate {
    let locationManager = CLLocationManager()
    
    func startBackgroundTracking() {
        locationManager.delegate = self
        
        // Request "Always" permission
        locationManager.requestAlwaysAndWhenInUseAuthorization()
        
        // Use significant location changes (efficient for iOS)
        locationManager.startMonitoringSignificantLocationChanges()
        
        // Fallback: timer for periodic updates (1-5s while driving)
        startPeriodicLocationUpdates(interval: 5)
    }
    
    func locationManager(_ manager: CLLocationManager,
                        didUpdateLocations locations: [CLLocation]) {
        for location in locations {
            let event = LocationEvent(
                lat: location.coordinate.latitude,
                lon: location.coordinate.longitude,
                speed: location.speed,
                accuracy: location.horizontalAccuracy,
                timestamp: location.timestamp
            )
            
            // Queue event for upload
            LocationQueue.shared.enqueue(event)
            
            // Adaptive: if moving fast, increase frequency
            if location.speed > 10 {
                updateSamplingInterval(1.0)  // 1s samples
            }
        }
    }
}
```

**Android Implementation (Foreground Service + Location Request)**

```kotlin
import android.location.Location
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationServices

class BackgroundTrackingService : Service() {
    private val fusedLocationClient by lazy {
        LocationServices.getFusedLocationProviderClient(this)
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForegroundService()
        startLocationUpdates()
        return START_STICKY
    }
    
    private fun startLocationUpdates() {
        val locationRequest = LocationRequest.create().apply {
            interval = 1000        // 1s while driving
            fastestInterval = 500
            priority = LocationRequest.PRIORITY_HIGH_ACCURACY
            maxWaitTime = 5000     // Batch if no movement for 5s
        }
        
        val locationCallback = object : LocationCallback() {
            override fun onLocationResult(locationResult: LocationResult) {
                for (location in locationResult.locations) {
                    val event = LocationEvent(
                        lat = location.latitude,
                        lon = location.longitude,
                        speed = location.speed,
                        accuracy = location.accuracy.toInt(),
                        timestamp = location.time
                    )
                    LocationQueue.shared.enqueue(event)
                }
            }
        }
        
        fusedLocationClient.requestLocationUpdates(
            locationRequest,
            locationCallback,
            Looper.getMainLooper()
        )
    }
    
    private fun startForegroundService() {
        val notification = NotificationCompat.Builder(this)
            .setContentTitle("Fleet Tracking Active")
            .setContentText("GPS tracking in progress")
            .setSmallIcon(R.drawable.ic_location)
            .build()
        
        startForeground(1, notification)
    }
}
```

**Offline Queue & Sync**

```typescript
// SQLite-based offline queue
interface LocationEvent {
  timestamp: number;
  latitude: number;
  longitude: number;
  speedKmh: number;
  batteryPercent: number;
  synced: boolean;
}

class LocationQueue {
  private db: SQLiteDatabase;
  
  async enqueue(event: LocationEvent) {
    await this.db.insert('location_events', {
      ...event,
      synced: false,
      createdAt: Date.now()
    });
  }
  
  async syncPending() {
    const pending = await this.db.query(
      'SELECT * FROM location_events WHERE synced = false LIMIT 100'
    );
    
    if (pending.length === 0) return;
    
    try {
      const response = await fetch('/api/v1/vehicles/{vehicleId}/locations/batch', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ locations: pending })
      });
      
      if (response.ok) {
        // Mark as synced
        await this.db.execute(
          'UPDATE location_events SET synced = true WHERE createdAt <= ?',
          [pending[pending.length - 1].createdAt]
        );
      }
    } catch (error) {
      console.log('Sync failed, will retry:', error);
      // Retry logic with exponential backoff
    }
  }
  
  // Sync on app resume, network connectivity change, or timer
  setupAutoSync() {
    AppState.addEventListener('change', (state) => {
      if (state === 'active') {
        this.syncPending();  // Resume
      }
    });
    
    NetInfo.addEventListener((state) => {
      if (state.isConnected && state.isInternetReachable) {
        this.syncPending();  // Network restored
      }
    });
    
    setInterval(() => this.syncPending(), 30000);  // Every 30s
  }
}
```

### Battery Optimization

**Adaptive Sampling:**

```typescript
// Adjust location update frequency based on movement and battery
class AdaptiveLocationSampler {
  getInterval(speedKmh: number, batteryPercent: number): number {
    // High speed + good battery: frequent updates (1-2s)
    if (speedKmh > 60 && batteryPercent > 0.30) return 1000;
    
    // Moderate speed: balanced (5-10s)
    if (speedKmh > 10 && batteryPercent > 0.20) return 5000;
    
    // Idling: reduce frequency (30-60s)
    if (speedKmh <= 1 && batteryPercent > 0.15) return 30000;
    
    // Critical battery: drastic reduction (5 min)
    if (batteryPercent < 0.15) return 300000;
    
    return 10000;  // Default: 10s
  }
}
```

**Geofencing for Offline Detection:**

```swift
// Wake app only when vehicle leaves current geofence
func startGeofenceMonitoring(radius: CLLocationDistance = 500) {
    let geofence = CLCircularRegion(
        center: lastKnownLocation,
        radius: radius,
        identifier: "truck_zone"
    )
    
    locationManager.startMonitoring(for: geofence)
    
    // On geofence exit: start high-frequency tracking
    // On geofence entry: reduce to balanced mode
}
```

### Security & Privacy

**Local Data Protection:**
```typescript
// Encrypt sensitive data in local storage
import AsyncStorage from '@react-native-async-storage/async-storage';
import EncryptedStorage from 'react-native-encrypted-storage';

// OAuth tokens → EncryptedStorage
await EncryptedStorage.setItem('auth_token', token);

// Location queue → SQLite with encryption
const db = new Database({
  name: 'locations.db',
  encrypted: true,
  password: 'device_specific_key'
});
```

**Device Attestation (prevent fake apps):**
```typescript
import { AttestationClient } from 'react-native-attestation';

async function attestDevice(): Promise<boolean> {
  const attestation = await AttestationClient.getAttestation();
  const response = await fetch('/api/v1/devices/attest', {
    method: 'POST',
    body: JSON.stringify(attestation)
  });
  return response.ok;
}
```

---

## Production Deployment Architecture

### Infrastructure as Code (Terraform)

```hcl
# main.tf: Kubernetes cluster on AWS EKS

terraform {
  required_version = ">= 1.0"
  
  backend "s3" {
    bucket  = "fleet-platform-state"
    key     = "prod/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 3.0"
  
  name = "fleet-platform-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  single_nat_gateway = false
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = "fleet-platform-prod"
  cluster_version = "1.28"
  
  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  # Worker node groups
  eks_managed_node_groups = {
    general = {
      name           = "general-nodes"
      instance_types = ["c6i.2xlarge"]
      desired_size   = 3
      min_size       = 3
      max_size       = 10
      
      tags = {
        Environment = "prod"
      }
    }
    
    memory_optimized = {
      name           = "memory-nodes"
      instance_types = ["r6i.2xlarge"]
      desired_size   = 2
      min_size       = 2
      max_size       = 6
      
      taints = [{
        key    = "workload"
        value  = "memory-intensive"
        effect = "NoSchedule"
      }]
    }
    
    spot = {
      name           = "spot-nodes"
      instance_types = ["t3.large", "t3a.large"]
      desired_size   = 5
      min_size       = 1
      max_size       = 20
      capacity_type  = "SPOT"
    }
  }
}

# RDS PostgreSQL
resource "aws_rds_cluster" "main" {
  cluster_identifier     = "fleet-platform-prod"
  engine                 = "aurora-postgresql"
  engine_version         = "15.3"
  
  database_name = "fleet_db"
  master_username = var.db_username
  master_password = random_password.db_password.result
  
  db_subnet_group_name            = aws_db_subnet_group.main.name
  vpc_security_group_ids          = [aws_security_group.rds.id]
  availability_zones              = data.aws_availability_zones.available.names
  
  backup_retention_period = 30
  preferred_backup_window = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"
  
  skip_final_snapshot       = false
  final_snapshot_identifier = "fleet-platform-prod-final-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  enabled_cloudwatch_logs_exports = ["postgresql"]
}

# RDS Multi-AZ Cluster Instances
resource "aws_rds_cluster_instance" "main" {
  count              = 2
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.r6i.xlarge"
  engine              = aws_rds_cluster.main.engine
  engine_version      = aws_rds_cluster.main.engine_version
  
  performance_insights_enabled = true
  monitoring_interval          = 60
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn
}

# Redis Cluster (ElastiCache)
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "fleet-platform-redis"
  engine               = "redis"
  node_type            = "cache.r6g.xlarge"
  num_cache_nodes      = 3
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  
  port                   = 6379
  subnet_group_name      = aws_elasticache_subnet_group.main.name
  security_group_ids     = [aws_security_group.redis.id]
  
  automatic_failover_enabled = true
  multi_az_enabled           = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}

# S3 for media (photos, exports)
resource "aws_s3_bucket" "media" {
  bucket = "fleet-platform-media-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "media" {
  bucket = aws_s3_bucket.media.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  bucket = aws_s3_bucket.media.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# RabbitMQ or Kafka (MSK)
resource "aws_msk_cluster" "main" {
  cluster_name           = "fleet-platform-kafka"
  kafka_version          = "3.6.0"
  number_of_broker_nodes = 3
  
  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    az_distribution = "DEFAULT"
    
    security_groups = [aws_security_group.kafka.id]
    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
  }
  
  encryption_info {
    encryption_in_transit {
      client_broker = "TLS_PLAINTEXT"
      in_cluster    = true
    }
    encryption_at_rest {
      data_volume_kms_key_id = aws_kms_key.kafka.arn
    }
  }
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  value = aws_rds_cluster.main.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}
```

### Kubernetes Deployments

**Ingestion Service (Deployment)**
```yaml
# ingestion-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: location-ingestion
  namespace: fleet-prod
spec:
  replicas: 5  # Start with 5, scale up to 50 based on load
  selector:
    matchLabels:
      app: location-ingestion
  template:
    metadata:
      labels:
        app: location-ingestion
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - location-ingestion
                topologyKey: kubernetes.io/hostname
      
      containers:
        - name: ingestion
          image: fleet-platform/location-ingestion:v1.0.0
          imagePullPolicy: IfNotPresent
          
          ports:
            - name: http
              containerPort: 8080
            - name: metrics
              containerPort: 9090
          
          env:
            - name: KAFKA_BROKERS
              value: "kafka.fleet-prod.svc.cluster.local:9092"
            - name: POSTGRES_URL
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: url
            - name: LOG_LEVEL
              value: "info"
          
          resources:
            requests:
              cpu: 1000m
              memory: 2Gi
            limits:
              cpu: 2000m
              memory: 4Gi
          
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 5
          
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
          
          securityContext:
            runAsNonRoot: true
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: location-ingestion-hpa
  namespace: fleet-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: location-ingestion
  minReplicas: 5
  maxReplicas: 50
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max
```

**API Service (Deployment)**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: fleet-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
    spec:
      containers:
        - name: api
          image: fleet-platform/api-service:v1.0.0
          ports:
            - name: http
              containerPort: 8000
          
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: url
            - name: REDIS_URL
              value: "redis://redis-cluster.fleet-prod.svc.cluster.local:6379"
          
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: 2000m
              memory: 2Gi
          
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: fleet-prod
spec:
  type: ClusterIP
  selector:
    app: api-service
  ports:
    - name: http
      port: 80
      targetPort: 8000

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### Multi-Tenant Data Isolation

```sql
-- Row-Level Security (Postgres)
-- Ensures tenants see only their own data

CREATE POLICY tenant_isolation_fleets
  ON fleets
  USING (org_id = current_setting('app.current_org_id')::uuid);

ALTER TABLE fleets ENABLE ROW LEVEL SECURITY;

-- Application middleware ensures org_id is set
-- Set before any query
SET app.current_org_id = 'org_abc123';
```

### Cost Estimation (Monthly)

| Component | Size | Cost/month |
|-----------|------|-----------|
| **Compute (EKS)** | 3 x c6i.2xlarge + 2 x r6i.2xlarge + 5x t3.large spot | $2,500 |
| **RDS (Aurora PostgreSQL)** | 2 x db.r6i.xlarge, 30-day backup | $1,800 |
| **TimescaleDB** | Managed (EBS gp3 1TB) | $400 |
| **Redis (ElastiCache)** | 3 x r6g.xlarge | $800 |
| **Kafka (MSK)** | 3 brokers x m5.large | $600 |
| **S3 (media storage)** | 100 TB cold tier | $2,300 |
| **Data Transfer (egress)** | ~500 GB/month | $400 |
| **Monitoring (Datadog)** | Custom metrics, APM | $500 |
| **SSL/TLS Certificates** | AWS Certificate Manager | Free |
| **DNS & CDN (CloudFront)** | For map tiles, API | $200 |
| **Backup & DR** | Cross-region snapshots | $300 |
| | **TOTAL** | **~$9,500/month** |

**Cost per vehicle (assuming 1000 vehicles):** ~$9.50/vehicle/month  
**Cost per vehicle (assuming 10,000 vehicles):** ~$0.95/vehicle/month

---

## Prioritized Feature Backlog

### MVP (Weeks 0–8): 200 Story Points

| Story ID | Feature | Description | Acceptance Criteria | Estimate | Priority |
|----------|---------|-------------|-------------------|----------|----------|
| **Foundation** | | | | | |
| FND-001 | Stabilize repo & CI | Fix build, add automated testing, setup monitoring | Builds pass, tests >80% coverage, logs in Datadog | 8 | P0 |
| FND-002 | Migrate SQLite → PostgreSQL | Export existing data, create production schema | Zero data loss, <30 min downtime, tested rollback | 13 | P0 |
| FND-003 | Add deterministic replay tool | Record events, replay trip state locally | Replay matches live logs exactly, bug discoverable | 8 | P0 |
| **Ingestion & Telemetry** | | | | | |
| ING-001 | Robust GPS ingestion API | POST /locations with validation, dedup, enrichment | Accept 10k/sec, <1% loss, ±5m accuracy stored | 21 | P0 |
| ING-002 | Device heartbeat monitoring | Detect offline devices, alert after 5 min timeout | Alerts created, tested with device offline sim | 8 | P0 |
| ING-003 | Time-series storage (TimescaleDB) | Migrate location events to TSDB, compression | Queries 100x faster, storage 60% cheaper | 13 | P0 |
| **Real-Time & Streaming** | | | | | |
| RT-001 | Kafka event bus | Setup multi-partition topics for each event type | <5 min lag end-to-end, 99.99% availability | 13 | P0 |
| RT-002 | WebSocket broker service | Real-time vehicle updates via WebSocket | <500ms median latency, p95 <2s, 5k concurrent | 21 | P0 |
| **Web Admin Dashboard** | | | | | |
| DASH-001 | Live map with vehicle markers | Leaflet integration, 1000+ vehicles, clustering | <500ms load, 60 FPS, no render errors | 21 | P0 |
| DASH-002 | Vehicle list & quick filter | Status, driver, geofence, region filters | Filter <200ms, list sorts instantly | 13 | P1 |
| DASH-003 | KPI summary cards | Online/offline counts, fuel burn, maintenance due | Cards refresh every 30s, math verified | 8 | P1 |
| DASH-004 | Trip replay with scrubber | Play/pause, speed control (1-4x), timeline scrub | Scrubber accurate to 1s, no memory leaks | 13 | P1 |
| **Driver Scoring** | | | | | |
| SCORE-001 | Real-time event detection | Harsh braking, overspeeding, idling sensors | Events captured within 5s of occurrence | 13 | P0 |
| SCORE-002 | Trip scoring algorithm | Calculate score 0-100 based on events | Score matches expected formula, tested with 100 trips | 13 | P0 |
| SCORE-003 | Driver scorecard UI | Driver view: recent trips, incidents, score trend | Loads in <2s, historical scores for 12 months | 13 | P1 |
| SCORE-004 | Dispute workflow (driver) | File dispute with notes & photo, track status | Dispute stored, driver can track status | 13 | P1 |
| SCORE-005 | Dispute workflow (admin) | Review disputes, approve/reject, adjust score | Disputes reviewed, scores adjusted, driver notified | 13 | P2 |
| **Alerts & Notifications** | | | | | |
| ALERT-001 | Alert deduplication service | Prevent spam: 1 alert per truck per 5s per type | Off-route tested: 1 alert per 5s max | 5 | P0 |
| ALERT-002 | Backend alert persistence | Create/read/resolve alerts via API | Alerts stored in DB, accessible in UI | 8 | P0 |
| ALERT-003 | Persistent alert panel | Bottom panel showing all unresolved alerts | Fetches every 10s, dedup by truck+type, max 10 | 13 | P1 |
| ALERT-004 | Critical alert KPI card | Count critical alerts, link to panel | Card shows accurate count, updates every 30s | 5 | P1 |
| **Mobile Driver App** | | | | | |
| MOBILE-001 | App skeleton & auth | OAuth2 PKCE login, SSO, token management | Login works, token persists, auto-refresh | 13 | P0 |
| MOBILE-002 | Permissions flow | Location, camera, storage with rationale screens | All permissions requested with clear messaging | 8 | P0 |
| MOBILE-003 | Shift start/end tracking | "Start Shift" button, high-accuracy GPS 30s, then balanced | Shift state tracked, GPS sampling verified | 13 | P0 |
| MOBILE-004 | Background GPS tracking | iOS + Android foreground service, offline queue | Tracks 8+ hours on 4000mAh battery | 21 | P0 |
| MOBILE-005 | Offline queue & sync | SQLite storage, batched HTTPS upload, conflict resolution | Queue survives app crash, syncs on connectivity | 21 | P0 |
| MOBILE-006 | Map view (simple) | Show vehicle location, recent trips | Map loads, location updates every 5s | 13 | P1 |
| MOBILE-007 | Trip history & dispute | View recent trips, file dispute with photo | Can file disputes, photo uploads | 13 | P1 |
| MOBILE-008 | Battery optimization | Adaptive sampling (1-300s), geofencing, low battery mode | <5% battery drain/hour balanced mode | 13 | P1 |
| **Security & Auth** | | | | | |
| SEC-001 | OAuth2 server | Authorization, token exchange, refresh flow | All flows tested, tokens secure, TTL enforced | 21 | P0 |
| SEC-002 | Role-based access control (RBAC) | Admin, manager, driver, viewer roles | Users can only access resources for their role | 13 | P0 |
| SEC-003 | TLS everywhere | Enforce TLS 1.3, cert pinning on mobile | All endpoints use TLS, no fallback to HTTP | 8 | P0 |
| SEC-004 | Audit logging | Immutable append-only log for admin actions | All mutations logged, tamper-proof, searchable | 13 | P1 |
| SEC-005 | Data encryption at rest | AES-256 for PII, sensitive data | Audit logs show no plaintext PII | 8 | P0 |
| SEC-006 | GDPR data export/deletion | Endpoints for data export & deletion | Can export all personal data, deletion removes from all systems | 13 | P1 |
| **Testing & QA** | | | | | |
| QA-001 | Ingestion load test | Simulate 10k vehicles, 1 event/sec each | Ingestion sustains 10k/sec, <0.1% loss | 13 | P1 |
| QA-002 | Mobile e2e test (UI) | Device emulator tests for core flows | Auth, shift tracking, dispute filing work end-to-end | 13 | P1 |
| QA-003 | Security audit prep | Address pen test findings, prep for external audit | Vulnerability scan clean, no P0 issues | 13 | P2 |
| **Pilot & Launch** | | | | | |
| PILOT-001 | Pilot onboarding docs | Checklist, training slides, support playbook | Pilots can self-serve with <2 hour onboarding | 13 | P1 |
| PILOT-002 | Pilot ROI dashboard | Fuel, time, maintenance savings calculator | Pilots can see projected ROI within 2 weeks | 13 | P1 |
| PILOT-003 | Production deployment | Terraform, K8s manifests, runbook | Can deploy changes in <10 min, rollback in <5 min | 21 | P1 |

**MVP Total: 208 story points**

---

### v1 (Weeks 9–20): 150 Story Points

| Story ID | Feature | Estimate | Priority |
|----------|---------|----------|----------|
| PRED-001 | Predictive maintenance prototype | 34 | P0 |
| PRED-002 | ML model training pipeline | 21 | P1 |
| ROI-001 | ROI dashboard with cost savings projections | 21 | P1 |
| COMPLIANCE-001 | HOS (Hours of Service) logging & alerts | 21 | P0 |
| COMPLIANCE-002 | Geofence automation (entry/exit actions) | 13 | P1 |
| BILLING-001 | Multi-tenant billing & metering | 34 | P0 |
| BILLING-002 | Usage dashboard (vehicles, events, storage) | 13 | P1 |
| SDK-001 | SDK for third-party integrations | 13 | P2 |
| ANALYTICS-001 | Advanced reporting (fuel burn, idle time, etc.) | 13 | P2 |

---

### v2 (Weeks 21–36): 100+ Story Points

| Story ID | Feature | Estimate | Priority |
|----------|---------|----------|----------|
| ML-001 | ETA prediction & dynamic routing | 34 | P0 |
| ML-002 | Fuel optimization algorithm | 21 | P1 |
| MARKETPLACE-001 | Fuel card integrations | 21 | P2 |
| MARKETPLACE-002 | Maintenance partner marketplace | 21 | P2 |
| WHITELABEL-001 | White-labeling & custom branding | 21 | P2 |
| SSO-001 | Enterprise SSO federation (SAML 2.0) | 13 | P2 |
| OFFLINE-MAP-001 | Offline map tiles for remote areas | 21 | P2 |

---

## Testing & QA Strategy

### Unit Testing

```typescript
// test/unit/alertManager.test.ts
import { AlertManager } from '../../src/services/alertManager';

describe('AlertManager', () => {
  let manager: AlertManager;
  
  beforeEach(() => {
    manager = new AlertManager();
  });
  
  describe('emitIfNew', () => {
    it('should return true on first emit for a truck/type', () => {
      const result = manager.emitIfNew('truck1', 'off-route', { distance: 100 });
      expect(result).toBe(true);
    });
    
    it('should return false if same truck/type emitted within 5s', () => {
      manager.emitIfNew('truck1', 'off-route', { distance: 100 });
      const result = manager.emitIfNew('truck1', 'off-route', { distance: 150 });
      expect(result).toBe(false);
    });
    
    it('should return true after 5s interval', async () => {
      manager.emitIfNew('truck1', 'off-route', { distance: 100 });
      await new Promise(r => setTimeout(r, 5100));
      const result = manager.emitIfNew('truck1', 'off-route', { distance: 150 });
      expect(result).toBe(true);
    });
    
    it('should not interfere with different alert types', () => {
      manager.emitIfNew('truck1', 'off-route', {});
      const result = manager.emitIfNew('truck1', 'overspeed', {});
      expect(result).toBe(true);
    });
  });
  
  describe('cleanup', () => {
    it('should remove old entries when exceeding 100 trucks', () => {
      for (let i = 0; i < 110; i++) {
        manager.emitIfNew(`truck${i}`, 'test', {});
      }
      manager.cleanup();
      // After cleanup, should have <100
      expect(Object.keys(manager.activeAlerts).length).toBeLessThan(100);
    });
  });
});
```

### Integration Testing

```typescript
// test/integration/locationIngestion.test.ts
import axios from 'axios';
import { PrismaClient } from '@prisma/client';

describe('Location Ingestion API', () => {
  const api = axios.create({ baseURL: 'http://localhost:8000/api' });
  const prisma = new PrismaClient();
  
  afterAll(async () => await prisma.$disconnect());
  
  it('should ingest location and persist to DB', async () => {
    const response = await api.post('/v1/vehicles/veh_test/locations', {
      timestamp: '2026-05-04T22:58:00Z',
      latitude: -18.9707,
      longitude: 32.6700,
      speedKmh: 50,
      accuracy_meters: 8,
      source: 'mobile'
    }, {
      headers: { Authorization: `Bearer ${testToken}` }
    });
    
    expect(response.status).toBe(202);
    
    // Verify in DB after small delay
    await new Promise(r => setTimeout(r, 100));
    const location = await prisma.location.findFirst({
      where: { vehicleId: 'veh_test' }
    });
    
    expect(location).toBeDefined();
    expect(location?.latitude).toBe(-18.9707);
  });
  
  it('should handle batch ingestion', async () => {
    const response = await api.post('/v1/vehicles/veh_batch/locations/batch', {
      locations: [
        { timestamp: '2026-05-04T22:55:00Z', latitude: -18.970, longitude: 32.669, speedKmh: 50 },
        { timestamp: '2026-05-04T22:56:00Z', latitude: -18.9707, longitude: 32.6700, speedKmh: 52.3 }
      ]
    }, {
      headers: { Authorization: `Bearer ${testToken}` }
    });
    
    expect(response.status).toBe(202);
    expect(response.data.itemsQueued).toBe(2);
  });
});
```

### End-to-End Testing (Mobile & Web)

```typescript
// test/e2e/driverApp.e2e.test.ts
import { by, device, expect as detox } from 'detox';

describe('Driver App - Shift Tracking E2E', () => {
  beforeAll(async () => {
    await device.launchApp({
      newInstance: true,
      permissions: { locations: 'always' }
    });
  });
  
  it('should authenticate and start shift', async () => {
    // Login
    await element(by.id('email-input')).typeText('driver@test.com');
    await element(by.id('password-input')).typeText('password123');
    await element(by.id('login-button')).tap();
    
    // Wait for dashboard
    await waitFor(element(by.text('Start Shift')))
      .toBeVisible()
      .withTimeout(5000);
    
    // Start shift
    await element(by.id('start-shift-button')).tap();
    
    // Verify GPS calibration screen
    await waitFor(element(by.text('Getting precise location...')))
      .toBeVisible()
      .withTimeout(1000);
    
    // Wait 30s for calibration
    await new Promise(r => setTimeout(r, 30000));
    
    // Verify shift active
    await detox.expect(element(by.text('Shift Active'))).toBeVisible();
  });
  
  it('should file a dispute', async () => {
    // Navigate to trip history
    await element(by.id('nav-history')).tap();
    
    // Tap first trip
    await element(by.id('trip-row-0')).tap();
    
    // Open dispute
    await element(by.text('Dispute This Trip')).tap();
    
    // Fill form
    await element(by.id('reason-dropdown')).tap();
    await element(by.text('GPS Error')).tap();
    
    await element(by.id('notes-input')).typeText('Construction blocked route');
    
    // Submit
    await element(by.id('submit-dispute-button')).tap();
    
    // Verify success
    await detox.expect(element(by.text('Dispute Submitted'))).toBeVisible();
  });
});
```

### Load Testing (k6)

```javascript
// test/load/location-ingestion-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const ingestionErrorRate = new Rate('ingestion_errors');
const ingestionDuration = new Trend('ingestion_duration');

export const options = {
  stages: [
    { duration: '2m', target: 100 },     // Ramp up to 100 vehicles
    { duration: '5m', target: 1000 },    // Ramp up to 1000 vehicles
    { duration: '10m', target: 10000 },  // Peak: 10k vehicles
    { duration: '5m', target: 1000 },    // Ramp down
    { duration: '2m', target: 0 }        // Cool down
  ],
  thresholds: {
    ingestion_errors: ['rate<0.001'],    // <0.1% error rate
    ingestion_duration: ['p95<1000'],    // <1s p95 latency
    http_req_duration: ['p99<2000']      // <2s p99
  }
};

export default function () {
  const vehicleId = `veh_${__VU}_${__ITER}`; // Unique vehicle per VU
  
  const payload = JSON.stringify({
    timestamp: new Date().toISOString(),
    latitude: -18.9707 + (Math.random() - 0.5) * 0.01,
    longitude: 32.6700 + (Math.random() - 0.5) * 0.01,
    speedKmh: Math.random() * 100,
    accuracy_meters: 8,
    source: 'mobile'
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${__ENV.TOKEN}`
    },
    tags: { name: 'LocationIngestion' }
  };
  
  const start = new Date();
  const res = http.post(
    `http://localhost:8000/api/v1/vehicles/${vehicleId}/locations`,
    payload,
    params
  );
  const duration = new Date() - start;
  
  ingestionDuration.add(duration);
  ingestionErrorRate.add(res.status !== 202);
  
  check(res, {
    'status is 202': (r) => r.status === 202,
    'response time < 1s': (r) => r.timings.duration < 1000,
  });
  
  sleep(0.5); // Simulate 2 events/sec per vehicle
}
```

### Monitoring & Observability (Prometheus Metrics)

```yaml
# prometheus-rules.yml
groups:
  - name: fleet_platform
    interval: 30s
    rules:
      - alert: HighIngestionErrorRate
        expr: rate(ingestion_errors_total[5m]) > 0.001
        for: 5m
        annotations:
          summary: "Ingestion error rate >0.1%"
      
      - alert: LocationQueryLatencyHigh
        expr: histogram_quantile(0.95, location_query_duration_ms) > 2000
        for: 10m
        annotations:
          summary: "Location queries p95 >2s"
      
      - alert: KafkaConsumerLagHigh
        expr: kafka_consumer_lag > 10000
        for: 10m
        annotations:
          summary: "Kafka consumer lag >10k messages"
      
      - alert: DatabaseConnectionPoolExhausted
        expr: db_connection_pool_active >= db_connection_pool_size * 0.9
        for: 5m
        annotations:
          summary: "DB connection pool >90% utilization"
```

---

## Security & Compliance Framework

### Security Checklist

- ✅ **Authentication**
  - [ ] OAuth2 server implemented (client credentials, authorization code)
  - [ ] PKCE flow for mobile apps
  - [ ] Token refresh logic with 1-hour TTL, 30-day refresh TTL
  - [ ] Session timeout after 15 min inactivity
  - [ ] Logout destroys all tokens

- ✅ **Authorization & Access Control**
  - [ ] RBAC with 4 roles: admin, manager, driver, viewer
  - [ ] Row-level security (RLS) in PostgreSQL
  - [ ] API endpoints check user role before returning data
  - [ ] No cross-tenant data leakage in queries

- ✅ **Encryption**
  - [ ] TLS 1.3 for all HTTP endpoints
  - [ ] Certificate pinning on mobile (prevent MITM)
  - [ ] AES-256 encryption at rest for:
    - PII (driver name, phone, email)
    - Photos (dispute, training)
    - Audit logs
  - [ ] Database encryption enabled (AWS RDS encryption)
  - [ ] S3 bucket encryption (AES-256)

- ✅ **Data Privacy & GDPR**
  - [ ] Data retention policy: default 12 months, configurable
  - [ ] GDPR data export endpoint (/api/v1/users/me/export)
  - [ ] GDPR data deletion endpoint (/api/v1/users/me/delete)
  - [ ] Right to be forgotten: automatic deletion after 30 days
  - [ ] Privacy policy displayed on signup
  - [ ] Consent logs for scoring, tracking

- ✅ **Audit & Logging**
  - [ ] Immutable audit log for all admin actions (create, update, delete)
  - [ ] Audit logs include: user ID, action, old/new values, timestamp, IP address
  - [ ] Audit logs signed with RSA-2048 to prevent tampering
  - [ ] Searchable audit logs via Elasticsearch
  - [ ] Retention: 3 years for compliance

- ✅ **API Security**
  - [ ] Rate limiting: 1000 req/min per tenant
  - [ ] WAF (ModSecurity) rules for common attacks (SQL injection, XSS)
  - [ ] API key rotation every 90 days
  - [ ] Scoped API keys (e.g., 'vehicles:read', 'locations:write')
  - [ ] No API keys in response bodies; only in header Authorization

- ✅ **Mobile Security**
  - [ ] No credentials stored in shared preferences; use KeyStore/Keychain
  - [ ] OAuth tokens encrypted in local storage
  - [ ] Location queue encrypted in SQLite
  - [ ] Device attestation: verify app is from official app store
  - [ ] Jailbreak/root detection: refuse to run on rooted devices
  - [ ] No hardcoded secrets in app binary

- ✅ **Infrastructure Security**
  - [ ] VPC with public/private subnets
  - [ ] Security groups: whitelist ingress ports (80, 443, 5432, 6379)
  - [ ] All inter-service communication uses mTLS
  - [ ] Database is private (no public IP)
  - [ ] Bastion host (jump box) for admin SSH access
  - [ ] OS patches applied weekly
  - [ ] Container images scanned for vulnerabilities

- ✅ **Compliance**
  - [ ] PCI-DSS: if handling payment cards (Stripe handles, we don't store)
  - [ ] SOC 2 Type II: annual audit, ongoing monitoring
  - [ ] GDPR: all above privacy/consent measures
  - [ ] CCPA: data export, deletion, right to know
  - [ ] Accessibility (WCAG 2.1 AA): alt text, color contrast, keyboard navigation

### Pen Testing Roadmap

**Phase 1 (Pre-MVP):** Internal security review by team
**Phase 2 (Pilot):** Third-party pen test of web API and mobile app
**Phase 3 (v1 launch):** Full SOC 2 audit; address any findings

---

## Observability & Monitoring

### Key Metrics (SLOs)

```yaml
# SLIs and Targets
objectives:
  - name: Ingestion Availability
    description: Location events reach backend successfully
    sli: ingestion_success_rate
    target: 0.999  # 99.9%
    alerting_threshold: 0.995  # Alert at 99.5%
  
  - name: API Latency
    description: API requests complete within latency budget
    sli: api_request_duration_p95
    target: 2000  # 2 seconds
    alerting_threshold: 1500  # Alert at 1.5s
  
  - name: Map Render Success
    description: Trip playback renders without errors
    sli: map_render_success_rate
    target: 0.999  # 99.9%
    alerting_threshold: 0.995
  
  - name: Realtime Update Latency
    description: WebSocket events arrive within latency budget
    sli: websocket_latency_p95
    target: 2000  # 2 seconds
    alerting_threshold: 1500
  
  - name: Mobile App Crash Rate
    description: App crash-free sessions
    sli: mobile_crash_free_rate
    target: 0.99  # 99%
    alerting_threshold: 0.98
```

### Prometheus Metrics

```yaml
# Sample queries for dashboards

# Ingestion Rate (events/sec)
rate(ingestion_events_total[1m])

# Ingestion Error Rate
rate(ingestion_errors_total[5m]) / rate(ingestion_events_total[5m])

# Location Query P95 Latency
histogram_quantile(0.95, rate(location_query_duration_ms_bucket[5m]))

# Vehicles Online Right Now
count(increase(vehicle_heartbeat_total[5m]) > 0)

# Active Drivers (mobile app)
count(mqtt_connected_clients{type="mobile"})

# Kafka Consumer Lag
kafka_consumer_lag{consumer_group="location_processor"}

# Database Connection Pool Usage
db_connection_pool_active / db_connection_pool_size
```

### Logging Strategy

```bash
# Structured JSON logs to CloudWatch/ELK
{
  "timestamp": "2026-05-04T22:58:00.123Z",
  "level": "error",
  "service": "location-ingestion",
  "pod": "ingestion-pod-abc123",
  "trace_id": "trace_xyz789",
  "span_id": "span_456",
  "message": "Failed to ingest location",
  "error": "Invalid accuracy",
  "vehicle_id": "veh_123",
  "fleet_id": "fleet_xyz",
  "user_id": "user_abc",
  "request_duration_ms": 150,
  "source": "mobile"
}

# Sensitive fields redacted
# phone_hash: "sha256(...)" not plaintext
# license_hash: "sha256(...)" not plaintext
# oauth_tokens: "*****" (last 4 chars only)
```

### Dashboards (Grafana)

**Dashboard 1: Ingestion Health**
- Graphs: events/sec, error rate, latency (p50, p95, p99)
- Status: green if SLO met, red if breached

**Dashboard 2: API Service**
- Endpoint latency breakdown
- Request rate by endpoint
- Error rate by endpoint

**Dashboard 3: Mobile App**
- Crash rate by version and OS
- Active users / MAU
- Background tracking success rate

**Dashboard 4: Database**
- Connection pool usage
- Query latency (p95)
- Replication lag (for multi-AZ)

---

## Migration & Pilot Strategy

### Pilot Cohort & Timeline

**Pilot Target:** 3 customers, 10–50 vehicles each, 8 weeks

**Customer Selection Criteria:**
- Established fleet (proven operations)
- Tech-forward leadership (willing to try new features)
- Accessible for onboarding calls and feedback
- Opportunity for case study / testimonial

### Pilot Onboarding Checklist

1. **Kickoff Call (Day 1)**
   - [ ] Intro to platform and team
   - [ ] Define success metrics (fuel savings %, driver improvement score, time)
   - [ ] Technical requirements review (devices, connectivity, permissions)
   - [ ] Timeline: 2-week shadow, 4-week live, 2-week validation

2. **Technical Setup (Days 2–5)**
   - [ ] Device compatibility check (phones, GPS trackers, OBD devices)
   - [ ] WiFi/cellular connectivity audit (for data sync)
   - [ ] Install app on pilot devices (or provide APK/IPA)
   - [ ] Create test accounts for each driver + manager
   - [ ] Verify GPS accuracy at key locations (depot, routes)

3. **Shadow Mode (Weeks 1–2)**
   - [ ] App running in background, collecting data
   - [ ] No scoring or alerts yet; read-only mode
   - [ ] Admin can verify data accuracy (compare to GPS device or manual logs)
   - [ ] Mobile app stability testing
   - [ ] Weekly check-in call

4. **Live Mode (Weeks 3–6)**
   - [ ] Enable driver scoring and alerts
   - [ ] Train drivers on dispute workflow
   - [ ] Admin trains on using dashboard (alerts, trip replay, reports)
   - [ ] Daily check-ins for first week; then weekly
   - [ ] Collect early feedback on UX

5. **Validation (Weeks 7–8)**
   - [ ] Measure ROI: fuel savings, time optimization, maintenance alerts
   - [ ] Collect testimonial and case study
   - [ ] Identify feature requests for roadmap
   - [ ] Success criteria met? → Convert to paid customer

### Pilot Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Data Accuracy | ±5m GPS vs. ground truth | Compare 10 trips to manual audit |
| Uptime | 99.5% minimum | Pilot operational hours without outages |
| Driver Adoption | 80%+ using app daily | App launch count / total drivers |
| Fuel Savings | ≥5% | (Baseline consumption - Pilot consumption) / Baseline |
| Speed Compliance | ≥15% improvement | (Overspeed incidents before - after) / before |
| Time Savings | ≥10 min/day per driver | (Baseline route time - Optimized time) / Baseline |
| Feature Requests | ≤3 critical blockers | Track and prioritize for v1 |
| Satisfaction | NPS ≥ 50 | Post-pilot survey |

### Rollback Plan

**Scenario 1: Critical Data Loss**
```
1. Detect: Alerts fire for >10% ingestion failures
2. Stop: Halt new data ingestion
3. Restore: Revert to last known good backup (hourly snapshots)
4. Validate: Run data consistency check (compare app log to DB)
5. Communicate: Notify customers, publish postmortem
```

**Scenario 2: Widespread Mobile App Crash**
```
1. Detect: Crash rate >5% reported via Sentry
2. Disable: Remotely disable new app versions in Playstore/AppStore (staged rollout)
3. Revert: Customers still on old version continue working
4. Fix: Hotfix in code, test, re-release
```

**Scenario 3: Security Breach**
```
1. Isolate: Take affected database offline
2. Notify: Alert security team and affected customers
3. Investigate: Forensic analysis (logs, audit trail)
4. Remediate: Change credentials, patch vulnerability
5. Verify: Re-scan for vulnerabilities before bringing back online
```

### Data Consistency Verification

```sql
-- Verify no data loss between device logs and backend
SELECT 
  vehicle_id,
  COUNT(*) as device_events,
  (SELECT COUNT(*) FROM locations 
   WHERE vehicle_id = d.vehicle_id) as db_events,
  ABS(COUNT(*) - (SELECT COUNT(*) FROM locations 
      WHERE vehicle_id = d.vehicle_id)) as delta
FROM device_logs d
GROUP BY vehicle_id
HAVING delta > 0;

-- Expected: delta = 0 (all events persisted)
-- If delta > 0: investigate connection issues, retry logic
```

---

## 12-Week Execution Roadmap

### Week 1: Foundation & Bug Fixes

**Goals:** Stabilize codebase, fix map rendering bugs, establish monitoring

**Tasks:**
- [ ] Audit existing codebase for bugs (GitHub issues, user reports)
- [ ] Fix critical bugs: map rendering, telemetry gaps (P0 issues)
- [ ] Setup CI/CD pipeline (GitHub Actions, Kubernetes deployment)
- [ ] Add test coverage for critical paths (>80% goal)
- [ ] Setup Prometheus + Grafana dashboards for infra monitoring
- [ ] Document architecture in wiki for team onboarding

**Deliverables:**
- Build passes, tests run automatically on PR
- Map renders 1000+ vehicles without lag
- Deterministic replay tool for debugging
- Team can reproduce any bug locally

**Acceptance Criteria:**
- ✅ Zero known P0 bugs
- ✅ >80% test coverage for API layer
- ✅ Dashboards show ingestion, API, database metrics
- ✅ Deployment runbook documented

---

### Week 2: Database Migration

**Goals:** Migrate from SQLite to PostgreSQL, setup multi-tenant foundation

**Tasks:**
- [ ] Design multi-tenant schema (org_id as partition key)
- [ ] Data migration: export SQLite, transform, load to PostgreSQL
- [ ] Verify zero data loss (row counts, checksums)
- [ ] Test rollback procedure
- [ ] Setup automated daily backups (S3)
- [ ] Performance test: queries on 1M location records

**Deliverables:**
- PostgreSQL in production, handling 100k locations
- Row-level security (RLS) policies enabled
- Automated backup & restore tested

**Acceptance Criteria:**
- ✅ All data migrated, checksums match
- ✅ Rollback tested and working
- ✅ Queries on large tables <500ms
- ✅ No downtime during migration (blue-green deployment)

---

### Week 3: Ingestion API v1.0

**Goals:** Build robust GPS ingestion with validation, dedup, enrichment

**Tasks:**
- [ ] Design and implement `/api/v1/vehicles/{id}/locations` POST endpoint
- [ ] Input validation: lat/lon bounds, timestamp, speed sanity checks
- [ ] Deduplication: ignore duplicate events within 1s
- [ ] Enrichment: add address lookup (reverse geocoding), speed limit check
- [ ] Rate limiting: 1000 req/min per tenant
- [ ] Setup Kafka to queue events for async processing
- [ ] Write integration tests

**Deliverables:**
- Location ingestion API, 100% tested
- Batch ingestion endpoint for offline queue
- Deduplication logic reduces data by ~30%

**Acceptance Criteria:**
- ✅ Accept 10k events/sec without queueing or loss
- ✅ Duplicates removed (verify in database)
- ✅ Rate limiting works (429 response when exceeded)
- ✅ Load test passes: 10k vehicles × 1 event/sec = no latency increase

---

### Week 4: WebSocket Real-Time & Mobile Auth

**Goals:** Build real-time event streaming; start mobile app with auth

**Tasks:**
- [ ] Implement WebSocket broker service (Node.js + Socket.io)
- [ ] Redis pub/sub for multi-pod message passing
- [ ] Subscribe to channels: `fleet:{id}`, `vehicle:{id}`
- [ ] Test: 5k concurrent connections, <500ms latency
- [ ] Mobile app skeleton: auth flow (OAuth2 PKCE), token storage
- [ ] Permission request screens (location, camera, storage)

**Deliverables:**
- WebSocket service handling real-time updates
- Mobile app can authenticate, request permissions, store token securely
- Live map updates every 2–5s via WebSocket

**Acceptance Criteria:**
- ✅ 5k concurrent WebSocket connections stable
- ✅ Event latency <500ms (median), <2s (p95)
- ✅ Mobile login flow works end-to-end
- ✅ Permissions survive app restart

---

### Week 5: Admin Dashboard Live Map

**Goals:** Build live map view showing all vehicles in real time

**Tasks:**
- [ ] Integrate Leaflet map library
- [ ] Implement vehicle marker clustering (prevent clutter at high zoom)
- [ ] Real-time vehicle location updates via WebSocket
- [ ] Vehicle status indicators: online (green), idle (yellow), offline (gray)
- [ ] Click drill-down to vehicle detail, trip history
- [ ] Test: render 1000 vehicles smoothly (60 FPS)
- [ ] Mobile map view (show current vehicle on map during shift)

**Deliverables:**
- Live map dashboard showing entire fleet
- Vehicle list with filters (status, driver, region)
- Trip playback with scrubber control

**Acceptance Criteria:**
- ✅ <500ms initial load on dashboard
- ✅ Smooth 60 FPS rendering with 1000+ vehicles
- ✅ No memory leaks after 1 hour of runtime
- ✅ Mobile map follows location updates every 5s

---

### Week 6: Mobile Background Tracking & Driver Scoring

**Goals:** Build background GPS tracking; calculate driver scores

**Tasks:**
- [ ] iOS background location (CoreLocation + Significant Changes)
- [ ] Android background tracking (Foreground Service)
- [ ] Offline queue: store locations in SQLite, sync when online
- [ ] Battery optimization: adaptive sampling (1–300s based on speed)
- [ ] Driver scoring: detect harsh braking, overspeeding, idling
- [ ] Real-time event detection in ingestion service
- [ ] Trip score calculation: 0–100 based on events

**Deliverables:**
- Mobile app tracks location in background for 8+ hours
- Trip completed → score calculated within 5s
- Driver can see scores and recent trips in app

**Acceptance Criteria:**
- ✅ Background tracking works after app close
- ✅ Offline queue syncs when connectivity restored
- ✅ Battery drain <5% per hour in balanced mode
- ✅ Trip score matches expected formula (tested with 100 trips)

---

### Week 7: Alerts & Dispute Workflow

**Goals:** Build alert system (dedup'd) and driver dispute flow

**Tasks:**
- [ ] Off-route detection: compare GPS to route, alert if >500m deviation
- [ ] Alert deduplication: 1 alert per truck per alert-type per 5s (already done)
- [ ] Backend alert persistence: create alerts in DB, store details
- [ ] Persistent alert panel: bottom UI component showing unresolved alerts
- [ ] Driver dispute: file, add notes/photos, track status
- [ ] Admin dispute review: approve/reject, adjust score, notify driver

**Deliverables:**
- Alerts appear in persistent panel, not just popups
- Drivers can dispute trips with photos
- Admin can review and resolve disputes

**Acceptance Criteria:**
- ✅ Off-route alert fires once per 5s per truck max
- ✅ Alerts persist through page refresh
- ✅ Driver can file dispute with photo in <2 min
- ✅ Admin dashboard shows pending disputes

---

### Week 8: Pilot Onboarding & Production Readiness

**Goals:** Prepare for first pilot customers; production deployment

**Tasks:**
- [ ] Finalize pilot onboarding checklist and docs
- [ ] Create pilot ROI calculator (fuel, time, maintenance projections)
- [ ] Terraform + Kubernetes manifests for production deployment
- [ ] Deployment runbook: how to deploy, rollback, debug
- [ ] Security audit: fix any found vulnerabilities
- [ ] Load test: 10k vehicles, 1 event/sec sustained
- [ ] Identify and onboard first 3 pilot customers
- [ ] Week 8: Start shadow mode with pilot 1

**Deliverables:**
- Pilot-ready platform, documented and tested
- Production infrastructure in AWS
- Pilot #1 operational in shadow mode
- Runbook for emergency procedures

**Acceptance Criteria:**
- ✅ Pilot onboarded in <2 hours per site
- ✅ Load test shows <1% errors, <1s p95 latency
- ✅ Deployment takes <10 min, rollback <5 min
- ✅ Pen test findings addressed (P0, P1 only)

---

### Weeks 9–12: v1 Features & Pilot Validation

**Sprint Goals:**

**Sprint 4 (Weeks 9–10): Predictive Maintenance**
- [ ] Ingest OBD-II data (or partner integrations)
- [ ] ML model: predict maintenance needs (engine hours, mileage patterns)
- [ ] Alerts: "Oil change due in 500 miles" or "Brake inspection recommended"
- [ ] Dashboard: show maintenance schedule for entire fleet
- [ ] Collect pilot feedback on alert accuracy

**Sprint 5 (Weeks 11–12): ROI Dashboard & Compliance**
- [ ] ROI dashboard: fuel savings, time saved, maintenance cost avoidance
- [ ] HOS logging: track driver hours, alert when approaching limits
- [ ] Geofence automation: auto-log entry/exit, trigger actions
- [ ] Compliance report: download HOS logs for audits
- [ ] Billing: implement multi-tenant metering (events, storage)

**Pilot Validation:**
- [ ] Pilots measure ROI (goal: ≥5% fuel savings)
- [ ] NPS survey: satisfaction score (goal: ≥50)
- [ ] Identify and prioritize feature requests
- [ ] Collect case study / testimonial

**Deliverables:**
- v1 feature set released
- Predictive maintenance module production-ready
- 3 pilot customers validated, 2+ ready to convert to paid
- ROI quantified and documented

**Acceptance Criteria:**
- ✅ 99.9% platform uptime (Weeks 9–12)
- ✅ <2s map update latency (p95)
- ✅ Pilot conversion rate ≥40% (2+ of 3)
- ✅ Average ROI per pilot ≥$5k/year
- ✅ NPS ≥50 from pilots

---

### Weeks 13–20: Scale & Enterprise Features (v1 Sprint 6–8)

**Overview:** Post-pilot, scale platform for broader market

**Sprint 6: Multi-Tenant Billing & Onboarding**
- Self-service signup flow
- Billing integration (Stripe)
- Usage metering and reporting
- Automated customer onboarding workflows

**Sprint 7: SDK & Integrations**
- Public API SDK (Python, JavaScript, Go)
- Partner integrations (fuel cards, maintenance providers)
- Webhook events for partners

**Sprint 8: Advanced Analytics**
- Fuel burn trends
- Driver performance leaderboards
- Cost per mile analysis
- Predictive ETA (for dispatch optimization)

---

## KPIs & Success Metrics

### Product KPIs (Pilot Phase)

| KPI | Target | Measurement | Owner |
|-----|--------|-------------|-------|
| **Pilot Onboarding Time** | ≤2 hours/site | Days to first GPS data visible in dashboard | CS/Ops |
| **Platform Uptime** | ≥99.9% | Ingestion service availability | Eng/SRE |
| **Map Update Latency (p95)** | ≤2 seconds | Time from GPS update to map display | Eng |
| **Mobile Crash Rate** | <0.5% | Crash-free session rate | Eng/Mobile |
| **Data Accuracy** | ±5m vs. ground truth | Spot check 10 trips vs. manual audit | QA |
| **Driver Adoption** | ≥80% | Daily active app launches / total drivers | Product |
| **Fuel Savings** | ≥5% | (Baseline - Pilot consumption) / Baseline | Sales/Pilot |
| **Time Savings** | ≥10 min/day | Route time reduction per driver | Sales/Pilot |
| **Pilot NPS** | ≥50 | Net Promoter Score from pilots | CS |
| **Pilot Conversion Rate** | ≥40% | Pilots → Paid customers | Sales |

### Engineering KPIs

| KPI | Target | Measurement |
|-----|--------|-------------|
| Test Coverage | >80% | Lines of code covered by tests |
| Build Time | <5 min | CI/CD pipeline duration |
| Deployment Frequency | 2–3x/week | Production releases per week |
| Mean Time to Recovery (MTTR) | <30 min | Time from incident to fix deployed |
| Bug Escape Rate | <0.1% | Bugs found in production / total bugs |
| Security Vulnerabilities | 0 P0, 0 P1 | Critical and high-severity findings |

---

## Pricing & Commercial Model

### Pricing Tiers

#### SMB (Small-Medium Business)

**Starter: $199/month**
- Up to 10 vehicles
- Basic GPS tracking
- Driver scoring (no dispute workflow)
- 30-day data retention
- Email support

**Growth: $499/month**
- Up to 50 vehicles
- Real-time tracking + alerts
- Full driver scoring + dispute workflow
- Trip playback
- 90-day data retention
- Phone + email support

**Professional: $1,299/month**
- Up to 250 vehicles
- All Growth features
- Predictive maintenance alerts
- ROI dashboard
- 12-month data retention
- Dedicated support + quarterly check-ins

#### Enterprise (Custom Pricing)

**Base: $3,000+/month**
- Unlimited vehicles
- All Professional features
- Custom integrations (OBD-II, telematics partners)
- White-labeling options
- SLA 99.9% uptime + priority support
- Dedicated account manager

**Add-Ons (per-tier):**
- Advanced Analytics: +$500/month
- API Access (per 1M events): +$100/month
- Custom Integrations: +$1000/month (one-time) + $200/month support
- White-Label: +$2000/month

### Pilot Program

**Offer: 60 Days Free**
- Full feature access (all tiers)
- Up to 50 vehicles
- Free onboarding + training
- Weekly support calls
- Success metrics defined upfront
- At end: convert to monthly plan at -20% discount if metrics met

---

## Sales One-Pager

---

### **FLEET MANAGEMENT PLATFORM – PILOT OFFER**

**Problem:** Fleets lose 10–20% to fuel waste, speeding, idle time, and reactive maintenance. Drivers lack accountability; fleet managers lack visibility.

**Solution:** Real-time GPS tracking + predictive maintenance + driver scoring = transparent, data-driven operations.

**Proof:** Early pilots show:
- **5–10% fuel savings** (optimized routes, reduced idling)
- **15–20% improvement** in speed compliance
- **$5,000+ per year** maintenance cost avoidance via predictive alerts

### **Key Differentiators**

✅ **Driver Dispute Workflow** – Drivers can challenge scores with evidence (photos, notes); builds trust  
✅ **Predictive Maintenance** – Alerts before breakdowns; reduces downtime  
✅ **ROI Dashboard** – Quantify savings in fuel, time, maintenance; justify investment  
✅ **Transparent Pricing** – No hidden fees; clear per-vehicle costs  
✅ **Privacy-First** – Drivers control when tracking pauses; compliance-ready (GDPR/CCPA)

### **Pilot Terms**

| Item | Details |
|------|---------|
| **Duration** | 60 days (2 weeks shadow, 4 weeks live, 2 weeks validation) |
| **Vehicles** | Up to 50 |
| **Cost** | Free |
| **Support** | Weekly check-ins + dedicated onboarding |
| **Success Metrics** | Fuel savings ≥5%, speed compliance ≥15% improvement, NPS ≥50 |
| **Conversion** | If metrics met: 20% discount on annual plan, else no obligation |

### **Quick Start**

1. **Week 1:** Kickoff call, technical audit, app deployment
2. **Week 2–3:** Shadow mode (read-only tracking, no alerts)
3. **Week 4–7:** Live mode (scoring, alerts, full features)
4. **Week 8:** Results review, ROI calculation, sign contract or iterate

### **Typical ROI (50 vehicles, 1-year term)**

| Item | Savings/Impact |
|------|-----------------|
| Fuel (5% reduction) | $50,000/year |
| Maintenance (15% fewer breakdowns) | $15,000/year |
| Time (10 min saved/day/driver) | $8,000/year |
| **Total Benefit** | **$73,000/year** |
| **Platform Cost (Growth tier)** | -$6,000/year |
| **Net ROI** | **$67,000 (11x return)** |

### **Next Steps**

📞 Schedule 30-min discovery call: [link]  
📧 Email pilot@fleet-platform.com  
🌐 Request demo: [link]

---

## Implementation Summary

This industrialization plan provides a **production-ready roadmap** for transforming the fleet management app into an enterprise-grade SaaS platform. Key highlights:

1. **MVP in 8 weeks:** Focus on core reliability, mobile app, and driver scoring
2. **Pilot-driven:** 3 customers validate product-market fit before broader launch
3. **Scalable architecture:** Kubernetes, multi-tenant Postgres, time-series storage, event streaming
4. **Security-first:** OAuth2, RBAC, encryption at rest/in-transit, audit logging
5. **Measurable success:** SLOs for uptime, latency, error rate; KPIs for ROI and NPS

**Recommended next steps:**
1. Review this plan with engineering, product, sales teams
2. Adjust scope/timeline based on team capacity
3. Establish pilot customer relationships (3 companies)
4. Begin Sprint 0 (Week 1) on bug fixes and foundation work
5. Weekly sync with leadership on roadmap progress

---

**Prepared by:** Product & Engineering Team  
**Version:** 1.0 (Ready for Execution)  
**Distribution:** Executive Leadership, Engineering, Product, Sales  
**Review Frequency:** Weekly sprint reviews; roadmap review every 4 weeks
