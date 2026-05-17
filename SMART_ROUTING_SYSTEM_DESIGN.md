# Smart Routing & Trail System – Fleet Management Platform
**A Production-Ready Design Superior to Google Maps for Fleet Operations**

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Data Model](#data-model)
4. [Routing Algorithm Detail](#routing-algorithm-detail)
5. [API Design](#api-design)
6. [Frontend Integration](#frontend-integration)
7. [Scalability & Performance](#scalability--performance)
8. [Reliability & Security](#reliability--security)
9. [Comparison vs Google Maps](#comparison-vs-google-maps)
10. [Implementation Roadmap](#implementation-roadmap)

---

## 1. Architecture Overview

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ React Leaflet UI │  │ Native Mobile    │  │ Web Browser  │  │
│  │ (Trail Viz)      │  │ (iOS/Android)    │  │ & Tablet     │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │
│           └──────────────────────┼────────────────────┘          │
│                                  │                                │
├──────────────────────────────────┼────────────────────────────────┤
│                     API GATEWAY (Kong/Traefik)                    │
│              ┌─────────────────────────────────┐                 │
│              │ Rate Limiting | Auth | Logging  │                 │
│              └──────────────┬────────────────────┘                │
│                             │                                     │
├──────────────────────────────┼────────────────────────────────────┤
│                    MICROSERVICES LAYER                            │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│  │ Route Service  │  │ Trail Service    │  │ Hazard Service │   │
│  │ (OSRM/Valhalla)│  │ (Map-Matching)   │  │ (ML Inference) │   │
│  └────────┬───────┘  └────────┬─────────┘  └────────┬───────┘   │
│           │                   │                     │             │
│  ┌────────┴────────┐  ┌──────┴──────────┐  ┌──────┴─────────┐   │
│  │ Traffic Service │  │ GPS Ingest Svc  │  │ SLA Monitor    │   │
│  │ (Real-time)    │  │ (Stream Proc.)  │  │ & Geofence     │   │
│  └────────┬───────┘  └────────┬────────┘  └────────┬───────┘   │
│           │                   │                     │             │
├──────────────────────────────┼───────────────────────┼──────────┤
│                    MESSAGE BUS (Apache Kafka/RabbitMQ)            │
│        Topics: gps.raw, gps.snapped, traffic.update,             │
│        alerts.hazard, route.updated, reroute.triggered           │
│                                                                   │
├────────────────────────────────────────────────────────────────────┤
│                      DATA LAYER                                   │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ TimescaleDB      │  │ Redis Cache  │  │ PostGIS (Road    │   │
│  │ (GPS Telemetry)  │  │ (Hot Data)   │  │ Network)         │   │
│  └──────────────────┘  └──────────────┘  └──────────────────┘   │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ InfluxDB         │  │ S3 (Vector   │  │ MongoDB          │   │
│  │ (Metrics/Traffic)│  │ Tiles)       │  │ (Dynamic Config) │   │
│  └──────────────────┘  └──────────────┘  └──────────────────┘   │
│                                                                   │
├────────────────────────────────────────────────────────────────────┤
│              EXTERNAL DATA SOURCES & ENGINES                       │
│  ┌───────────┐  ┌────────────────┐  ┌──────────┐  ┌────────────┐ │
│  │ OpenStreet│  │ Weather API    │  │ Traffic  │  │ ML Model   │ │
│  │ Map (OSM) │  │ (Weather Stack)│  │ Feed API │  │ (TensorFlow)
│  │ Elevation │  │ Air Quality    │  │ (HERE,   │  │ Inference  │ │
│  │ Data      │  │ OpenWeather    │  │ TomTom)  │  │ Service    │ │
│  └───────────┘  └────────────────┘  └──────────┘  └────────────┘ │
│                                                                   │
└────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **API Gateway** | Authentication, rate limiting, load balancing | Kong, Traefik |
| **Route Service** | Optimal route calculation | OSRM/Valhalla/GraphHopper |
| **Trail Service** | GPS trace map-matching to roads | Valhalla Map-Match API |
| **Traffic Service** | Real-time & predictive traffic | Kafka Streams, ML models |
| **Hazard Service** | AI-detected road hazards (curves, grades, school zones) | TensorFlow, PyTorch |
| **GPS Ingest Service** | High-throughput GPS point ingestion | Apache Kafka, Faust |
| **SLA Monitor** | Geofence violations, SLA breach detection | GeoPandas, PostGIS |
| **Message Bus** | Event-driven async communication | Kafka or RabbitMQ |
| **Cache Layer** | Sub-millisecond route/tile caching | Redis, Memcached |
| **Time-Series DB** | 100+ million GPS points/day | TimescaleDB, InfluxDB |
| **Road Network DB** | Spatial indexing of road geometry | PostGIS + PostgreSQL |

### Data Flow (Real-Time Route Update)

1. **GPS Ingestion** → Raw GPS point arrives at `/gps` endpoint
2. **Stream Processing** → Kafka captures point, triggers map-matching
3. **Map-Matching** → Trail service snaps point to nearest road segment
4. **Aggregation** → Points batched into polyline (locally cached)
5. **Traffic Polling** → Traffic service queries upstream traffic APIs
6. **Re-routing Decision** → If traffic increases delay >5 min, trigger re-route
7. **Route Optimization** → Query Route Service with updated vehicle state
8. **Broadcast Update** → WebSocket push new route to all clients
9. **Persistence** → Store snapped points to TimescaleDB, cache to Redis

---

## 2. Technology Stack

### Backend Services

| Layer | Recommended Tech | Alternative | Rationale |
|-------|------------------|-------------|-----------|
| **API Gateway** | Kong/Traefik + Lua plugins | AWS API Gateway | Kong scales horizontally; Lua for custom rate limits |
| **Route Engine** | Valhalla (GraphQL API) | OSRM, GraphHopper | Valhalla supports truck profiles, elevation, time-window constraints |
| **Map-Matching** | Valhalla Map-Matching API | Mapbox, GraphHopper | Valhalla's MM algorithm is tuned for 1 Hz GPS (drift tolerance) |
| **Language** | Python 3.11 (FastAPI/asyncio) | Node.js, Go | Python: rich ML/GIS libraries (Shapely, Fiona, Geopandas); FastAPI is async-native |
| **Message Queue** | Apache Kafka | RabbitMQ, AWS SNS | Kafka: replay-able topics, stream processing (Kafka Streams, Faust) |
| **Stream Processing** | Faust (Python) | Kafka Streams (Java), Spark | Faust integrates seamlessly with Python backend; low latency |
| **Cache** | Redis (cluster mode) | Memcached | Redis: supports sorted sets for spatial queries, pub/sub for real-time |
| **Time-Series DB** | TimescaleDB (PostgreSQL) | InfluxDB, Prometheus | TimescaleDB: SQL interface, ACID, GPS polyline geom support |
| **Spatial DB** | PostGIS + PostgreSQL | MongoDB+Geospatial | PostGIS: mature road network routing, index types (GIST, BRIN) |
| **Search/Analytics** | Elasticsearch + Kibana | Splunk | Free tier, log aggregation, alerting rules |
| **ML/AI** | TensorFlow 2.x + FastAPI | PyTorch, Hugging Face | TensorFlow: production deployment via TF Serving; congestion prediction |
| **Container Orchestration** | Kubernetes (EKS) | Docker Swarm, Nomad | K8s: industry standard, auto-scaling, RBAC |

### Frontend Stack

| Layer | Tech | Version | Purpose |
|-------|------|---------|---------|
| **Framework** | React | 18.2+ | Component-based, hooks for state |
| **Mapping** | Leaflet + React-Leaflet | 4.x | Lightweight, vector tile support via Mapbox GL |
| **Map Tiles** | Mapbox Vector Tiles (MVT) | XYZ | Pre-rendered tiles in S3 for offline fallback |
| **Real-Time** | TanStack Query + WebSocket | v4+ | Polling + push; fallback to SSE |
| **State Mgmt** | Zustand | 4.x | Lightweight, minimal boilerplate |
| **UI Components** | Tailwind CSS + shadcn/ui | Latest | Accessible, consistent theming |
| **Offline Maps** | Leaflet Offline, leaflet-tilelayer-offline | Latest | Pre-download tiles; localStorage + IndexedDB |
| **Voice** | Web Audio API + TTS | Native | Browser-native text-to-speech (no external dependency) |

### Infrastructure & Deployment

| Service | Tech Stack | Configuration |
|---------|-----------|-----------------|
| **Container Registry** | Docker + AWS ECR | Private registry, auto-scan for vulnerabilities |
| **CI/CD** | GitHub Actions + ArgoCD | GitOps workflow; auto-deploy on main merge |
| **Monitoring** | Prometheus + Grafana + AlertManager | Custom dashboards for route latency, GPS ingest rate |
| **Logging** | ELK Stack or Loki + Promtail | Structured JSON logs; 30-day retention |
| **APM** | Jaeger Distributed Tracing | Trace GPS → map-match → route latency |
| **VCS** | GitHub | PR-based code review, commit hooks |

### External APIs & Data

| Service | Purpose | Pricing Model |
|---------|---------|----------------|
| **OpenStreetMap (via Overpass API)** | Road geometry, POI data | Free (rate-limited) |
| **Elevation API (OpenElevation)** | Terrain analysis for fuel consumption | Free |
| **Weather API (OpenWeatherMap/WeatherStack)** | Real-time weather for congestion prediction | Freemium |
| **Traffic Feed (HERE/TomTom/Google)** | Real-time traffic speed data | Per-request or subscription |
| **Air Quality (OpenWeatherMap AQI)** | Hazard detection (air quality alerts) | Freemium |

---

## 3. Data Model

### Core Tables/Collections

#### 3.1 Vehicles Table (PostgreSQL)

```sql
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fleet_id UUID NOT NULL REFERENCES fleets(id),
    vehicle_id VARCHAR(50) UNIQUE NOT NULL, -- e.g., "TRUCK-001"
    vehicle_type VARCHAR(20) NOT NULL, -- 'truck', 'van', 'motorcycle'
    
    -- Physical properties
    max_weight_kg FLOAT NOT NULL, -- Gross vehicle weight rating
    current_load_kg FLOAT DEFAULT 0,
    cargo_type VARCHAR(100), -- 'perishable', 'hazmat', 'general'
    max_speed_kmh INT DEFAULT 120,
    
    -- Constraints
    max_daily_hours INT DEFAULT 11, -- EU driving regulations
    current_hours_today INT DEFAULT 0,
    last_break_timestamp TIMESTAMP,
    
    -- Current state
    status VARCHAR(20) DEFAULT 'idle', -- 'idle', 'in_transit', 'at_dock'
    last_gps_timestamp TIMESTAMP,
    last_gps_lat FLOAT,
    last_gps_lon FLOAT,
    
    -- Fuel & efficiency
    fuel_type VARCHAR(20), -- 'diesel', 'electric', 'hybrid'
    fuel_consumption_l_per_100km FLOAT DEFAULT 25.0,
    current_fuel_liters FLOAT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vehicles_fleet_id ON vehicles(fleet_id);
CREATE INDEX idx_vehicles_status ON vehicles(status);
```

#### 3.2 GPS Points (TimescaleDB Hypertable)

```sql
CREATE TABLE gps_points (
    time TIMESTAMP NOT NULL,
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
    road_segment_id INT, -- References road_segments.id in PostGIS
    distance_to_road_m FLOAT,
    
    -- Derived metrics
    acceleration_ms2 FLOAT,
    harsh_braking BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT create_hypertable('gps_points', 'time', if_not_exists => TRUE);
CREATE INDEX idx_gps_vehicle_time ON gps_points (vehicle_id, time DESC);
CREATE INDEX idx_gps_geom ON gps_points USING GIST (ll_to_earth(lat, lon));
```

#### 3.3 Snapped Trail Polylines (PostGIS + TimescaleDB)

```sql
CREATE TABLE trail_polylines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    
    -- Polyline geometry (LineString of snapped points)
    geom GEOMETRY(LineString, 4326) NOT NULL,
    
    -- Metadata
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    point_count INT DEFAULT 0,
    total_distance_km FLOAT,
    total_time_seconds INT,
    
    -- Quality metrics
    map_match_confidence FLOAT DEFAULT 1.0, -- 0-1 score
    raw_vs_snapped_distance_m FLOAT, -- How much raw GPS deviated
    
    -- Status
    finalized BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trail_vehicle_time ON trail_polylines (vehicle_id, start_time DESC);
CREATE INDEX idx_trail_geom ON trail_polylines USING GIST (geom);
```

#### 3.4 Routes Table (Planned Routes)

```sql
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    
    -- Route metadata
    origin_lat FLOAT NOT NULL, origin_lon FLOAT NOT NULL,
    destination_lat FLOAT NOT NULL, destination_lon FLOAT NOT NULL,
    waypoints JSONB DEFAULT '[]', -- Array of intermediate stops
    
    -- Route polyline (before departing)
    planned_polyline GEOMETRY(LineString, 4326),
    planned_distance_km FLOAT,
    planned_duration_seconds INT,
    planned_fuel_liters FLOAT,
    
    -- Constraints used
    route_profile VARCHAR(50), -- 'fastest', 'fuel_optimal', 'avoidhazards'
    avoid_hazards BOOLEAN DEFAULT TRUE,
    max_grade_pct FLOAT DEFAULT 15.0, -- Max slope for truck
    
    -- Status
    status VARCHAR(20) DEFAULT 'planned', -- 'planned', 'active', 'completed', 'cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Actual vs. planned
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
```

#### 3.5 Traffic Events (Real-Time)

```sql
CREATE TABLE traffic_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event location
    geom GEOMETRY(Point, 4326) NOT NULL,
    lat FLOAT NOT NULL, lon FLOAT NOT NULL,
    
    -- Event type
    event_type VARCHAR(50) NOT NULL, -- 'accident', 'construction', 'congestion', 'weather'
    severity VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high'
    description TEXT,
    
    -- Impact
    speed_kmh_expected INT, -- Expected speed on affected segment
    delay_minutes INT, -- Estimated delay
    affected_polyline GEOMETRY(LineString, 4326), -- Road(s) affected
    
    -- Duration
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimated_end_time TIMESTAMP,
    
    -- Source
    source VARCHAR(50), -- 'waze_api', 'google_traffic', 'ml_prediction', 'user_report'
    confidence FLOAT DEFAULT 0.8, -- 0-1
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_traffic_geom ON traffic_events USING GIST (geom);
CREATE INDEX idx_traffic_created_at ON traffic_events (created_at DESC);
```

#### 3.6 Hazards Table (AI-Detected)

```sql
CREATE TABLE hazards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Hazard location
    geom GEOMETRY(Point, 4326) NOT NULL,
    lat FLOAT NOT NULL, lon FLOAT NOT NULL,
    road_segment_id INT,
    
    -- Hazard classification
    hazard_type VARCHAR(50) NOT NULL,
    -- 'sharp_curve', 'steep_descent', 'sharp_ascent', 'school_zone', 
    -- 'railroad_crossing', 'bridge', 'tunnel', 'low_clearance', 'weight_limit'
    
    severity_score FLOAT DEFAULT 0.5, -- 0-1, ML-derived
    description TEXT,
    
    -- Spatial extent
    affected_polyline GEOMETRY(LineString, 4326),
    recommendation TEXT, -- e.g., "Reduce speed to 40 km/h"
    
    -- OSM metadata
    osm_tags JSONB, -- Raw OSM tags for reference
    
    -- Data quality
    confidence FLOAT DEFAULT 0.85,
    source VARCHAR(50) DEFAULT 'ml_inference', -- 'osm', 'gps_analytics', 'ml_inference'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hazards_geom ON hazards USING GIST (geom);
CREATE INDEX idx_hazards_type ON hazards (hazard_type);
```

#### 3.7 Geofences & SLA Milestones (MongoDB)

```json
{
  "_id": "ObjectId(...)",
  "fleet_id": "fleet-uuid-001",
  "name": "Harare Distribution Hub",
  "geom": {
    "type": "Polygon",
    "coordinates": [[17.8252, -17.8252], [...], ...]
  },
  "geofence_type": "checkpoint", // or "dock", "exclusion", "slowzone"
  "sla_rules": [
    {
      "route_id": "route-uuid-001",
      "target_arrival_time": "2026-04-30T14:00:00Z",
      "window_minutes_early": 5,
      "window_minutes_late": 10,
      "penalty_per_minute": 2.50, // USD
      "notification_threshold_minutes": 5
    }
  ],
  "alert_thresholds": {
    "dwell_time_max_minutes": 30,
    "speed_limit_kmh": 40
  },
  "created_at": "2026-04-29T10:00:00Z",
  "updated_at": "2026-04-29T10:00:00Z"
}
```

#### 3.8 SLA Breach Log (TimescaleDB)

```sql
CREATE TABLE sla_breaches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    route_id UUID NOT NULL REFERENCES routes(id),
    geofence_id UUID NOT NULL,
    
    -- Breach details
    expected_arrival TIMESTAMP NOT NULL,
    actual_arrival TIMESTAMP,
    late_by_minutes INT,
    
    -- Impact
    penalty_usd FLOAT,
    customer_notification_sent BOOLEAN DEFAULT FALSE,
    driver_alert_sent BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT create_hypertable('sla_breaches', 'created_at', if_not_exists => TRUE);
```

#### 3.9 Road Segments (PostGIS - Static)

```sql
CREATE TABLE road_segments (
    id BIGINT PRIMARY KEY, -- OSM way ID
    
    -- Geometry
    geom GEOMETRY(LineString, 4326) NOT NULL,
    length_m FLOAT NOT NULL,
    
    -- Road properties
    osm_way_id BIGINT,
    name VARCHAR(255),
    highway_type VARCHAR(30), -- 'motorway', 'primary', 'secondary', 'residential'
    
    -- Dynamic properties (updated by traffic feed)
    speed_limit_kmh INT DEFAULT 50,
    current_avg_speed_kmh INT,
    congestion_level VARCHAR(20) DEFAULT 'unknown', -- 'free', 'slow', 'congested', 'blocked'
    
    -- Truck-specific properties
    truck_allowed BOOLEAN DEFAULT TRUE,
    hazmat_allowed BOOLEAN DEFAULT TRUE,
    weight_limit_tons FLOAT,
    height_limit_m FLOAT,
    
    -- Elevation data
    avg_grade_pct FLOAT, -- Average slope
    max_grade_pct FLOAT,
    elevation_change_m INT,
    
    -- Fuel efficiency model (learned from fleet data)
    fuel_efficiency_factor FLOAT DEFAULT 1.0, -- <1 = better efficiency
    
    -- Hazard flags (pre-computed)
    has_sharp_curves BOOLEAN DEFAULT FALSE,
    has_steep_descent BOOLEAN DEFAULT FALSE,
    has_sharp_ascent BOOLEAN DEFAULT FALSE,
    is_school_zone BOOLEAN DEFAULT FALSE,
    has_railroad_crossing BOOLEAN DEFAULT FALSE,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_road_geom ON road_segments USING GIST (geom);
CREATE INDEX idx_road_highway_type ON road_segments (highway_type);
```

---

## 4. Routing Algorithm Detail

### 4.1 Map-Matching Algorithm

**Problem:** Raw GPS points zigzag; we need to snap them to actual road geometry.

**Solution:** Hidden Markov Model (HMM) based map-matching, as implemented in Valhalla.

#### Pseudocode: HMM Map-Matching

```python
def map_match_gps_trace(gps_points: List[GPSPoint], road_network: RoadNetwork) -> List[SnappedPoint]:
    """
    Match raw GPS points to road segments using HMM.
    
    HMM States: Possible road segments within emission_threshold of each GPS point.
    Observations: Noisy GPS coordinates.
    Transition Probability: How likely to move from segment A to B (distance, connectivity).
    Emission Probability: How likely GPS point came from that segment (distance to segment).
    """
    
    emission_threshold_m = 50  # GPS points within 50m of road
    matched_trace = []
    
    # 1. Candidate generation: Find road segments within threshold of each GPS point
    candidates_per_point = []
    for gps in gps_points:
        candidates = road_network.query_nearest_segments(
            lat=gps.lat, lon=gps.lon, radius_m=emission_threshold_m, limit=5
        )
        # Sort by distance to get best candidates first
        candidates = sorted(candidates, key=lambda c: c['distance_m'])
        candidates_per_point.append(candidates)
    
    # 2. HMM Viterbi algorithm: Find most likely path through road segments
    
    # Initialize: First GPS point has equal probability for all candidates
    prev_probabilities = {}
    prev_best_path = {}
    
    for candidate in candidates_per_point[0]:
        seg_id = candidate['segment_id']
        # Emission probability: How far is GPS from this segment?
        emission_prob = math.exp(-candidate['distance_m']**2 / (2 * 10**2))  # Gaussian
        prev_probabilities[seg_id] = emission_prob
        prev_best_path[seg_id] = [seg_id]
    
    # Forward pass: For each subsequent GPS point
    for i in range(1, len(gps_points)):
        curr_probabilities = {}
        curr_best_path = {}
        
        for curr_candidate in candidates_per_point[i]:
            curr_seg_id = curr_candidate['segment_id']
            max_prob = 0.0
            best_prev_seg = None
            
            # Check transition from all previous segments
            for prev_seg_id, prev_prob in prev_probabilities.items():
                # Transition probability: How connected are these segments?
                transition_prob = compute_transition_prob(
                    prev_seg_id, curr_seg_id, 
                    gps_points[i-1], gps_points[i], 
                    road_network
                )
                
                # Emission probability: How far is curr GPS from curr segment?
                emission_prob = math.exp(-curr_candidate['distance_m']**2 / (2 * 10**2))
                
                # Viterbi: Combined probability
                combined_prob = prev_prob * transition_prob * emission_prob
                
                if combined_prob > max_prob:
                    max_prob = combined_prob
                    best_prev_seg = prev_seg_id
            
            if max_prob > 0:
                curr_probabilities[curr_seg_id] = max_prob
                curr_best_path[curr_seg_id] = prev_best_path[best_prev_seg] + [curr_seg_id]
        
        prev_probabilities = curr_probabilities
        prev_best_path = curr_best_path
    
    # 3. Backtrack: Extract best path
    if prev_probabilities:
        best_final_seg = max(prev_probabilities, key=prev_probabilities.get)
        best_path_seg_ids = prev_best_path[best_final_seg]
        
        # 4. Interpolate: Get snapped coordinates on road segments
        for i, gps_point in enumerate(gps_points):
            if i < len(best_path_seg_ids):
                seg_id = best_path_seg_ids[i]
                segment = road_network.get_segment(seg_id)
                
                # Project GPS point onto segment
                snapped_coords = segment.project_point(gps_point.lat, gps_point.lon)
                
                matched_trace.append(SnappedPoint(
                    original_lat=gps_point.lat,
                    original_lon=gps_point.lon,
                    snapped_lat=snapped_coords['lat'],
                    snapped_lon=snapped_coords['lon'],
                    segment_id=seg_id,
                    confidence=prev_probabilities[seg_id],
                    distance_to_road_m=snapped_coords['distance']
                ))
    
    return matched_trace


def compute_transition_prob(prev_seg_id: int, curr_seg_id: int, 
                            prev_gps: GPSPoint, curr_gps: GPSPoint,
                            road_network: RoadNetwork) -> float:
    """
    Compute probability of transitioning from prev_seg to curr_seg.
    
    Considers:
    - Is there a valid route between segments?
    - How far is the GPS movement vs. road distance?
    """
    # Query shortest path between segments
    route = road_network.route_between_segments(prev_seg_id, curr_seg_id)
    
    if not route:
        return 0.01  # Segments not connected
    
    # GPS movement distance
    gps_distance = haversine_distance(
        prev_gps.lat, prev_gps.lon, 
        curr_gps.lat, curr_gps.lon
    )
    
    # Road distance
    road_distance = route['distance_m']
    
    # How well do they match?
    # If GPS move ~= road distance, high prob; if very different, low prob
    distance_ratio = gps_distance / road_distance if road_distance > 0 else 1.0
    
    # Transition prob peaks at ratio ~1, decays on both sides
    transition_prob = math.exp(-0.5 * (distance_ratio - 1.0)**2)
    
    return transition_prob
```

---

### 4.2 Fast Route Calculation with Fuel & Traffic Awareness

#### Algorithm: Dijkstra with AI-Augmented Edge Weights

```python
def compute_optimal_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    vehicle: Vehicle,
    route_profile: str = 'fuel_optimal',  # or 'fastest', 'avoidhazards'
    time_of_day: datetime = None,
    avoid_hazards: bool = True
) -> Route:
    """
    Compute optimal route using Dijkstra with multi-factor edge weights.
    
    Edge cost function incorporates:
    - Base travel time
    - Traffic congestion
    - Fuel consumption (depends on road grade, vehicle weight)
    - Hazard penalties
    - Vehicle constraints (max grade, height, weight limits)
    """
    
    if time_of_day is None:
        time_of_day = datetime.now()
    
    # 1. Snap origin/destination to nearest road segments
    origin_seg = road_network.snap_to_segment(origin[0], origin[1])
    dest_seg = road_network.snap_to_segment(destination[0], destination[1])
    
    if not origin_seg or not dest_seg:
        raise ValueError("Origin or destination not on road network")
    
    # 2. Build priority queue (min-heap by cost)
    import heapq
    pq = [(0, origin_seg['segment_id'])]
    visited = set()
    distances = {origin_seg['segment_id']: 0}
    came_from = {}
    
    # 3. Dijkstra iteration
    while pq:
        current_cost, current_seg_id = heapq.heappop(pq)
        
        if current_seg_id in visited:
            continue
        visited.add(current_seg_id)
        
        # Reached destination?
        if current_seg_id == dest_seg['segment_id']:
            break
        
        # Explore neighbors
        neighbors = road_network.get_adjacent_segments(current_seg_id)
        
        for neighbor_seg_id in neighbors:
            if neighbor_seg_id in visited:
                continue
            
            neighbor_seg = road_network.get_segment(neighbor_seg_id)
            
            # Check vehicle constraints
            if not vehicle_can_traverse(vehicle, neighbor_seg):
                continue  # Vehicle too heavy, too tall, hazmat not allowed, etc.
            
            # 4. Compute edge cost (multi-factor)
            edge_cost = compute_edge_cost(
                segment=neighbor_seg,
                vehicle=vehicle,
                profile=route_profile,
                time_of_day=time_of_day,
                avoid_hazards=avoid_hazards,
                traffic_cache=traffic_cache,
                hazard_cache=hazard_cache
            )
            
            new_cost = current_cost + edge_cost
            
            if neighbor_seg_id not in distances or new_cost < distances[neighbor_seg_id]:
                distances[neighbor_seg_id] = new_cost
                came_from[neighbor_seg_id] = current_seg_id
                heapq.heappush(pq, (new_cost, neighbor_seg_id))
    
    # 5. Reconstruct path
    if dest_seg['segment_id'] not in came_from and dest_seg['segment_id'] != origin_seg['segment_id']:
        raise ValueError("No route found to destination")
    
    path_seg_ids = []
    current = dest_seg['segment_id']
    while current in came_from:
        path_seg_ids.insert(0, current)
        current = came_from[current]
    path_seg_ids.insert(0, origin_seg['segment_id'])
    
    # 6. Convert segments to polyline + compute metrics
    polyline = segments_to_polyline(path_seg_ids)
    total_distance = sum(road_network.get_segment(sid)['length_m'] for sid in path_seg_ids) / 1000
    total_duration_seconds = compute_route_duration(path_seg_ids, time_of_day)
    total_fuel_liters = compute_route_fuel_consumption(path_seg_ids, vehicle)
    
    route = Route(
        id=str(uuid.uuid4()),
        vehicle_id=vehicle.id,
        origin_lat=origin[0],
        origin_lon=origin[1],
        destination_lat=destination[0],
        destination_lon=destination[1],
        planned_polyline=polyline,
        planned_distance_km=total_distance,
        planned_duration_seconds=total_duration_seconds,
        planned_fuel_liters=total_fuel_liters,
        route_profile=route_profile,
        status='planned',
        created_at=datetime.now()
    )
    
    return route


def compute_edge_cost(segment: RoadSegment, vehicle: Vehicle, profile: str,
                       time_of_day: datetime, avoid_hazards: bool,
                       traffic_cache: Dict, hazard_cache: Dict) -> float:
    """
    Multi-factor edge cost function.
    
    Cost = base_time + traffic_delay + fuel_cost + hazard_penalty
    """
    
    base_time_hours = segment['length_m'] / 1000 / segment['speed_limit_kmh']
    
    # 1. Traffic penalty (real-time)
    traffic_event = traffic_cache.get(segment['id'])
    traffic_multiplier = 1.0
    if traffic_event:
        # Congestion reduces speed
        traffic_multiplier = 1.0 + (traffic_event['delay_minutes'] / 60) / base_time_hours \
                               if base_time_hours > 0 else 1.0
    
    # 2. Fuel cost (vehicle weight, road grade, efficiency model)
    fuel_consumption_liters = compute_segment_fuel(vehicle, segment)
    fuel_cost_hours = fuel_consumption_liters / vehicle['fuel_consumption_l_per_100km'] * 100
    
    if profile == 'fuel_optimal':
        fuel_weight = 0.6  # Prioritize fuel economy
    else:
        fuel_weight = 0.2
    
    # 3. Hazard penalty
    hazard_penalty = 0.0
    if avoid_hazards:
        hazards = hazard_cache.get(segment['id'], [])
        for hazard in hazards:
            # Steep descent: add time (slow down to 30 km/h)
            if hazard['type'] == 'steep_descent':
                hazard_penalty += segment['length_m'] / 1000 / 30  # Hours
            # Sharp curve: add time (slow to 40 km/h)
            elif hazard['type'] == 'sharp_curve':
                hazard_penalty += segment['length_m'] / 1000 / 40
            # School zone: add time (slow to 20 km/h)
            elif hazard['type'] == 'school_zone':
                hazard_penalty += segment['length_m'] / 1000 / 20
    
    # 4. Combine into edge cost
    edge_cost = (
        base_time_hours * traffic_multiplier +
        fuel_weight * fuel_cost_hours +
        hazard_penalty
    )
    
    return edge_cost


def compute_segment_fuel(vehicle: Vehicle, segment: RoadSegment) -> float:
    """
    Estimate fuel consumption for a segment considering:
    - Vehicle weight
    - Road grade (uphill burns more fuel)
    - Road type efficiency
    """
    
    # Base consumption (from vehicle spec)
    base_l_per_100km = vehicle['fuel_consumption_l_per_100km']
    
    # Adjust for current load
    load_factor = vehicle['current_load_kg'] / vehicle['max_weight_kg']  # 0 to 1
    
    # Adjust for grade (uphill = more fuel)
    grade_factor = 1.0
    if segment['avg_grade_pct'] > 0:
        # Rough estimate: 5% grade ~10% more fuel
        grade_factor = 1.0 + (segment['avg_grade_pct'] / 50)
    
    # Adjust for road type efficiency (motorway ~5% more efficient than residential)
    efficiency_factor = segment.get('fuel_efficiency_factor', 1.0)
    
    # Compute consumption for this segment
    segment_length_km = segment['length_m'] / 1000
    fuel_liters = (base_l_per_100km / 100) * segment_length_km * load_factor * grade_factor * efficiency_factor
    
    return fuel_liters


def vehicle_can_traverse(vehicle: Vehicle, segment: RoadSegment) -> bool:
    """
    Check if vehicle meets constraints for this segment.
    """
    
    # Weight limit
    if segment.get('weight_limit_tons'):
        vehicle_weight_tons = (vehicle['max_weight_kg'] + vehicle['current_load_kg']) / 1000
        if vehicle_weight_tons > segment['weight_limit_tons']:
            return False
    
    # Height limit
    if segment.get('height_limit_m'):
        if vehicle.get('height_m', 3.5) > segment['height_limit_m']:
            return False
    
    # Truck allowed?
    if vehicle['vehicle_type'] == 'truck' and not segment.get('truck_allowed', True):
        return False
    
    # Hazmat allowed?
    if vehicle.get('cargo_type') == 'hazmat' and not segment.get('hazmat_allowed', True):
        return False
    
    return True
```

---

### 4.3 Real-Time Re-Routing Trigger

```python
async def monitor_and_reroutete_vehicle(vehicle_id: str, active_route: Route):
    """
    Continuously monitor active route; trigger re-route if conditions change significantly.
    """
    
    reroute_thresholds = {
        'delay_threshold_minutes': 5,  # If delay > 5 min, re-route
        'traffic_incident_distance_m': 1000,  # Incident within 1 km of route
        'sla_breach_warning_minutes': 15  # If SLA breach likely
    }
    
    while active_route.status == 'active':
        vehicle = await get_vehicle(vehicle_id)
        
        # 1. Check current traffic ahead
        traffic_ahead = await query_traffic_on_route(
            polyline=active_route.planned_polyline,
            distance_ahead_km=10
        )
        
        # 2. Estimate current delay
        if traffic_ahead:
            max_delay = max(te['delay_minutes'] for te in traffic_ahead)
            if max_delay > reroute_thresholds['delay_threshold_minutes']:
                logger.info(f"Vehicle {vehicle_id}: Traffic delay {max_delay}min, triggering re-route")
                
                # Get current vehicle position
                current_pos = (vehicle['last_gps_lat'], vehicle['last_gps_lon'])
                
                # Compute new optimal route from current position to destination
                new_route = await compute_optimal_route(
                    origin=current_pos,
                    destination=(active_route.destination_lat, active_route.destination_lon),
                    vehicle=vehicle,
                    route_profile=active_route.route_profile,
                    time_of_day=datetime.now(),
                    avoid_hazards=active_route.avoid_hazards
                )
                
                # Compare savings
                time_saved_seconds = active_route.planned_duration_seconds - new_route.planned_duration_seconds
                
                if time_saved_seconds > 300:  # >5 min savings
                    # Push new route to vehicle
                    await broadcast_route_update(
                        vehicle_id=vehicle_id,
                        new_route=new_route,
                        reason='traffic_detected'
                    )
                    active_route = new_route
        
        # 3. Check SLA breach risk
        estimated_arrival = datetime.now() + timedelta(seconds=active_route.planned_duration_seconds)
        if hasattr(active_route, 'sla_deadline'):
            time_to_deadline = (active_route.sla_deadline - estimated_arrival).total_seconds() / 60
            
            if 0 < time_to_deadline < reroute_thresholds['sla_breach_warning_minutes']:
                logger.warning(f"Vehicle {vehicle_id}: SLA breach in {time_to_deadline} min")
                
                # Try to find faster route
                new_route = await compute_optimal_route(
                    origin=(vehicle['last_gps_lat'], vehicle['last_gps_lon']),
                    destination=(active_route.destination_lat, active_route.destination_lon),
                    vehicle=vehicle,
                    route_profile='fastest',  # Override to fastest
                    avoid_hazards=False,  # Be aggressive
                    time_of_day=datetime.now()
                )
                
                if new_route.planned_duration_seconds < (time_to_deadline * 60):
                    await broadcast_route_update(
                        vehicle_id=vehicle_id,
                        new_route=new_route,
                        reason='sla_at_risk',
                        priority='high'
                    )
        
        # Wait before next check
        await asyncio.sleep(30)  # Check every 30 seconds
```

---

## 5. API Design

### REST Endpoints

#### 5.1 Route Calculation

```
POST /api/v2/routes/calculate

Request:
{
  "origin": {
    "lat": 17.8252,
    "lon": 25.2753
  },
  "destination": {
    "lat": 17.8832,
    "lon": 25.8232
  },
  "vehicle_id": "TRUCK-001",
  "profile": "fuel_optimal",  // or "fastest", "avoid_hazards"
  "waypoints": [
    {
      "lat": 17.83,
      "lon": 25.80,
      "type": "delivery",
      "dwell_time_minutes": 15
    }
  ],
  "time_of_day": "2026-04-30T14:00:00Z",
  "avoid_hazards": true,
  "constraints": {
    "max_grade_pct": 12,
    "max_toll_cost": 50.00
  }
}

Response (200 OK):
{
  "route_id": "route-uuid-0001",
  "vehicle_id": "TRUCK-001",
  "polyline": {
    "type": "LineString",
    "coordinates": [[25.2753, 17.8252], [25.276, 17.826], ...]
  },
  "distance_km": 142.5,
  "duration_seconds": 9400,
  "estimated_fuel_liters": 35.2,
  "estimated_cost_usd": 127.50,
  "profile": "fuel_optimal",
  "segments": [
    {
      "segment_id": 123456,
      "name": "Harare-Bulawayo Road",
      "length_km": 50.2,
      "speed_limit_kmh": 120,
      "hazards": [
        {
          "type": "steep_descent",
          "severity": 0.7,
          "recommendation": "Reduce speed to 40 km/h, monitor brakes"
        }
      ]
    }
  ],
  "traffic_events": [
    {
      "type": "congestion",
      "location": { "lat": 17.85, "lon": 25.81 },
      "delay_minutes": 3,
      "description": "Construction on A9 motorway"
    }
  ],
  "alternatives": [
    {
      "route_id": "route-alt-001",
      "polyline": {...},
      "distance_km": 150.0,
      "duration_seconds": 8800,
      "fuel_liters": 38.5,
      "reason": "Faster route via A8"
    }
  ]
}
```

#### 5.2 GPS Ingest (Streaming)

```
POST /api/v2/gps

Request (batch):
{
  "vehicle_id": "TRUCK-001",
  "points": [
    {
      "lat": 17.8252,
      "lon": 25.2753,
      "timestamp": "2026-04-30T10:15:32.123Z",
      "altitude_m": 1450,
      "speed_kmh": 85.5,
      "accuracy_m": 8.2,
      "heading_deg": 125
    },
    {
      "lat": 17.8255,
      "lon": 25.2760,
      "timestamp": "2026-04-30T10:15:35.456Z",
      "altitude_m": 1452,
      "speed_kmh": 85.0,
      "accuracy_m": 7.9,
      "heading_deg": 124
    }
  ]
}

Response (202 Accepted):
{
  "status": "accepted",
  "points_ingested": 2,
  "latest_point": {
    "lat": 17.8255,
    "lon": 25.2760,
    "snapped_lat": 17.82553,
    "snapped_lon": 25.27598,
    "road_segment_id": 789012,
    "map_match_confidence": 0.94
  },
  "vehicle_state": {
    "vehicle_id": "TRUCK-001",
    "last_gps_timestamp": "2026-04-30T10:15:35.456Z",
    "status": "in_transit",
    "current_route_id": "route-uuid-001",
    "time_to_destination_seconds": 8105,
    "sla_status": "on_track"
  }
}
```

#### 5.3 Snapped Trail

```
GET /api/v2/trails/{vehicle_id}?start_time=...&end_time=...&simplify=true

Response (200 OK):
{
  "vehicle_id": "TRUCK-001",
  "trail_id": "trail-uuid-001",
  "start_time": "2026-04-30T08:00:00Z",
  "end_time": "2026-04-30T16:30:00Z",
  "polyline": {
    "type": "LineString",
    "coordinates": [[25.2753, 17.8252], [25.276, 17.826], ..., [25.8232, 17.8832]]
  },
  "raw_points_count": 1247,
  "snapped_points_count": 1247,
  "total_distance_km": 142.5,
  "total_time_seconds": 30600,
  "map_match_quality": {
    "avg_confidence": 0.945,
    "points_off_road_5m": 12,
    "points_off_road_10m": 3
  },
  "events": [
    {
      "timestamp": "2026-04-30T10:15:32Z",
      "type": "harsh_braking",
      "severity": 0.8,
      "location": { "lat": 17.85, "lon": 25.81 },
      "deceleration_ms2": -2.3
    },
    {
      "timestamp": "2026-04-30T12:00:00Z",
      "type": "dwell",
      "location": { "lat": 17.86, "lon": 25.82 },
      "duration_seconds": 900
    }
  ]
}
```

#### 5.4 Hazards Query

```
GET /api/v2/hazards?bounds=25.2,17.8,25.9,17.9&hazard_type=sharp_curve,steep_descent

Response (200 OK):
{
  "bbox": { "min_lon": 25.2, "min_lat": 17.8, "max_lon": 25.9, "max_lat": 17.9 },
  "hazard_count": 23,
  "hazards": [
    {
      "hazard_id": "hazard-001",
      "type": "sharp_curve",
      "location": { "lat": 17.85, "lon": 25.81 },
      "severity_score": 0.75,
      "description": "Hairpin turn (radius 45m) on Matenje Pass",
      "recommendation": "Reduce speed to 35 km/h, watch for oncoming traffic",
      "affected_polyline": {
        "type": "LineString",
        "coordinates": [[25.809, 17.849], [25.811, 17.851]]
      },
      "confidence": 0.92,
      "source": "ml_inference"
    },
    {
      "hazard_id": "hazard-002",
      "type": "steep_descent",
      "location": { "lat": 17.87, "lon": 25.82 },
      "severity_score": 0.68,
      "grade_pct": 8.5,
      "recommendation": "Use engine braking, avoid riding brakes",
      "confidence": 0.88,
      "source": "osm_elevation"
    }
  ]
}
```

#### 5.5 Traffic Events (Real-Time Subscription)

```
WebSocket: ws://api.fleet.local/api/v2/traffic/subscribe

Subscribe message:
{
  "action": "subscribe",
  "bounds": {
    "min_lon": 25.2,
    "min_lat": 17.8,
    "max_lon": 25.9,
    "max_lat": 17.9
  },
  "event_types": ["accident", "congestion", "construction"]
}

Server pushes events:
{
  "event_id": "traffic-001",
  "type": "congestion",
  "location": { "lat": 17.85, "lon": 25.81 },
  "severity": "high",
  "delay_minutes": 5,
  "description": "A9 motorway congestion due to construction",
  "affected_polyline": {
    "type": "LineString",
    "coordinates": [[25.809, 17.849], [25.811, 17.851]]
  },
  "affected_vehicles": ["TRUCK-001", "TRUCK-003"],
  "timestamp": "2026-04-30T14:22:00Z",
  "source": "google_traffic_feed"
}
```

#### 5.6 SLA Monitoring

```
GET /api/v2/vehicles/{vehicle_id}/sla-status

Response (200 OK):
{
  "vehicle_id": "TRUCK-001",
  "active_route_id": "route-uuid-001",
  "current_position": { "lat": 17.85, "lon": 25.81 },
  "milestones": [
    {
      "geofence_name": "Harare Hub",
      "target_arrival": "2026-04-30T14:00:00Z",
      "estimated_arrival": "2026-04-30T13:55:00Z",
      "status": "on_track",
      "eta_seconds": -300,
      "penalty_usd": 0
    },
    {
      "geofence_name": "Gweru Distribution",
      "target_arrival": "2026-04-30T15:30:00Z",
      "estimated_arrival": "2026-04-30T15:35:00Z",
      "status": "at_risk",
      "eta_seconds": 300,
      "penalty_usd": 5.00,
      "recommended_action": "Increase speed by 5 km/h or take alternative route via A9"
    }
  ],
  "total_potential_penalty": 5.00,
  "breach_count": 1
}
```

---

## 6. Frontend Integration

### 6.1 Route Display Component (React)

```jsx
import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, GeoJSON, Marker, Popup } from 'react-leaflet';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import L from 'leaflet';

export function RouteMapVisualization({ vehicleId, routeId }) {
  const [route, setRoute] = useState(null);
  const [trail, setTrail] = useState(null);
  const [hazards, setHazards] = useState([]);
  const [trafficEvents, setTrafficEvents] = useState([]);
  const queryClient = useQueryClient();

  // Fetch route
  const { data: routeData } = useQuery({
    queryKey: ['route', routeId],
    queryFn: () => fetch(`/api/v2/routes/${routeId}`).then(r => r.json()),
    refetchInterval: 5000,
  });

  // Fetch live trail
  const { data: trailData } = useQuery({
    queryKey: ['trail', vehicleId],
    queryFn: () => fetch(`/api/v2/trails/${vehicleId}?simplify=true`).then(r => r.json()),
    refetchInterval: 10000,
  });

  // Fetch hazards along route
  useEffect(() => {
    if (routeData?.polyline) {
      const bbox = computeBoundingBox(routeData.polyline);
      fetch(`/api/v2/hazards?bounds=${bbox.minLon},${bbox.minLat},${bbox.maxLon},${bbox.maxLat}`)
        .then(r => r.json())
        .then(data => setHazards(data.hazards));
    }
  }, [routeData]);

  // Real-time traffic subscription
  useEffect(() => {
    if (!routeData?.polyline) return;

    const bbox = computeBoundingBox(routeData.polyline);
    const ws = new WebSocket('ws://api.fleet.local/api/v2/traffic/subscribe');

    ws.onopen = () => {
      ws.send(JSON.stringify({
        action: 'subscribe',
        bounds: { minLon: bbox.minLon, minLat: bbox.minLat, maxLon: bbox.maxLon, maxLat: bbox.maxLat },
        event_types: ['accident', 'congestion', 'construction'],
      }));
    };

    ws.onmessage = (event) => {
      const trafficEvent = JSON.parse(event.data);
      setTrafficEvents(prev => [...prev.filter(e => e.event_id !== trafficEvent.event_id), trafficEvent]);
      
      // Trigger re-route if necessary
      if (trafficEvent.severity === 'high') {
        queryClient.invalidateQueries({ queryKey: ['route', routeId] });
      }
    };

    return () => ws.close();
  }, [routeData, routeId, queryClient]);

  if (!routeData) return <div>Loading route...</div>;

  const routePolylineCoords = routeData.polyline.coordinates.map(([lon, lat]) => [lat, lon]);
  const trailPolylineCoords = trailData?.polyline?.coordinates?.map(([lon, lat]) => [lat, lon]) || [];

  return (
    <MapContainer center={[17.8252, 25.2753]} zoom={8} style={{ height: '100%', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OSM'
      />

      {/* Planned Route (blue, dashed) */}
      <Polyline
        positions={routePolylineCoords}
        pathOptions={{
          color: '#0066cc',
          weight: 3,
          dashArray: '5, 5',
          opacity: 0.7,
        }}
        eventHandlers={{
          mouseover: (e) => e.target.setStyle({ weight: 5 }),
          mouseout: (e) => e.target.setStyle({ weight: 3 }),
        }}
      >
        <Popup>
          <div>
            <p><strong>Planned Route</strong></p>
            <p>Distance: {routeData.distance_km.toFixed(1)} km</p>
            <p>Duration: {(routeData.duration_seconds / 3600).toFixed(1)} hours</p>
            <p>Fuel: {routeData.estimated_fuel_liters.toFixed(1)} L</p>
          </div>
        </Popup>
      </Polyline>

      {/* Actual Trail (green, solid) */}
      {trailData && (
        <Polyline
          positions={trailPolylineCoords}
          pathOptions={{
            color: '#00aa00',
            weight: 2,
            opacity: 0.8,
          }}
        >
          <Popup>
            <div>
              <p><strong>Actual Trail</strong></p>
              <p>Distance: {trailData.total_distance_km.toFixed(1)} km</p>
              <p>Duration: {(trailData.total_time_seconds / 3600).toFixed(1)} hours</p>
            </div>
          </Popup>
        </Polyline>
      )}

      {/* Hazards (red markers) */}
      {hazards.map(hazard => (
        <Marker
          key={hazard.hazard_id}
          position={[hazard.location.lat, hazard.location.lon]}
          icon={L.icon({
            iconUrl: getHazardIcon(hazard.type),
            iconSize: [32, 32],
          })}
        >
          <Popup>
            <div>
              <p><strong>{hazard.type.replace(/_/g, ' ')}</strong></p>
              <p>Severity: {(hazard.severity_score * 100).toFixed(0)}%</p>
              <p>{hazard.recommendation}</p>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Traffic Events (orange) */}
      {trafficEvents.map(event => (
        <Marker
          key={event.event_id}
          position={[event.location.lat, event.location.lon]}
          icon={L.icon({
            iconUrl: 'data:image/svg+xml,...', // Orange marker
            iconSize: [32, 32],
          })}
        >
          <Popup>
            <div>
              <p><strong>{event.type}</strong></p>
              <p>Delay: {event.delay_minutes} min</p>
              <p>{event.description}</p>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Waypoints */}
      {routeData.segments?.map((segment, idx) => (
        <Marker key={idx} position={[segment.start_lat, segment.start_lon]}>
          <Popup>{segment.name}</Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

function getHazardIcon(hazardType) {
  const iconMap = {
    sharp_curve: 'hazard-curve.svg',
    steep_descent: 'hazard-descent.svg',
    school_zone: 'hazard-school.svg',
    railroad_crossing: 'hazard-rail.svg',
  };
  return iconMap[hazardType] || 'hazard-generic.svg';
}

function computeBoundingBox(linestring) {
  const lats = linestring.coordinates.map(c => c[1]);
  const lons = linestring.coordinates.map(c => c[0]);
  return {
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
  };
}
```

### 6.2 Route Planner UI (Control Panel)

```jsx
import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

export function RoutePlannerPanel() {
  const [origin, setOrigin] = useState(null);
  const [destination, setDestination] = useState(null);
  const [profile, setProfile] = useState('fuel_optimal');
  const [vehicleId, setVehicleId] = useState('TRUCK-001');
  const [avoidHazards, setAvoidHazards] = useState(true);
  const [alternatives, setAlternatives] = useState([]);

  const calculateRoute = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/v2/routes/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin,
          destination,
          vehicle_id: vehicleId,
          profile,
          avoid_hazards: avoidHazards,
        }),
      });
      return response.json();
    },
    onSuccess: (data) => {
      setAlternatives(data.alternatives || []);
    },
  });

  return (
    <div className="p-4 bg-white shadow-lg rounded-lg">
      <h2 className="text-xl font-bold mb-4">Route Planner</h2>

      <div className="space-y-3">
        {/* Vehicle Selection */}
        <div>
          <label className="block text-sm font-semibold mb-1">Vehicle</label>
          <select
            value={vehicleId}
            onChange={(e) => setVehicleId(e.target.value)}
            className="w-full border rounded px-2 py-1"
          >
            <option value="TRUCK-001">TRUCK-001 (Volvo)</option>
            <option value="TRUCK-002">TRUCK-002 (Scania)</option>
          </select>
        </div>

        {/* Route Profile */}
        <div>
          <label className="block text-sm font-semibold mb-1">Route Profile</label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="radio"
                value="fuel_optimal"
                checked={profile === 'fuel_optimal'}
                onChange={(e) => setProfile(e.target.value)}
                className="mr-2"
              />
              <span>⛽ Fuel Optimal (minimize consumption)</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="fastest"
                checked={profile === 'fastest'}
                onChange={(e) => setProfile(e.target.value)}
                className="mr-2"
              />
              <span>⚡ Fastest (minimize time)</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="avoid_hazards"
                checked={profile === 'avoid_hazards'}
                onChange={(e) => setProfile(e.target.value)}
                className="mr-2"
              />
              <span>🚨 Avoid Hazards (safer route)</span>
            </label>
          </div>
        </div>

        {/* Avoid Hazards Toggle */}
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={avoidHazards}
            onChange={(e) => setAvoidHazards(e.target.checked)}
            className="mr-2"
          />
          <span className="text-sm font-semibold">Avoid sharp curves & steep descents</span>
        </label>

        {/* Calculate Button */}
        <button
          onClick={() => calculateRoute.mutate()}
          disabled={!origin || !destination || calculateRoute.isPending}
          className="w-full bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700 disabled:bg-gray-400"
        >
          {calculateRoute.isPending ? 'Calculating...' : 'Calculate Route'}
        </button>
      </div>

      {/* Results */}
      {calculateRoute.data && (
        <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200">
          <p className="font-semibold">📍 Primary Route</p>
          <p className="text-sm">Distance: {calculateRoute.data.distance_km.toFixed(1)} km</p>
          <p className="text-sm">Duration: {(calculateRoute.data.duration_seconds / 3600).toFixed(1)} h</p>
          <p className="text-sm">Fuel: {calculateRoute.data.estimated_fuel_liters.toFixed(1)} L (${calculateRoute.data.estimated_cost_usd.toFixed(2)})</p>
        </div>
      )}

      {/* Alternatives */}
      {alternatives.length > 0 && (
        <div className="mt-3 space-y-2">
          <p className="font-semibold text-sm">Alternative Routes</p>
          {alternatives.map((alt, idx) => (
            <div key={idx} className="p-2 bg-gray-100 rounded text-sm">
              <p><strong>{alt.reason}</strong></p>
              <p>Distance: {alt.distance_km.toFixed(1)} km | Time: {(alt.duration_seconds / 3600).toFixed(1)} h | Fuel: {alt.fuel_liters.toFixed(1)} L</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 6.3 Offline Support (Service Worker + IndexedDB)

```javascript
// offline-routes.js - Caching strategy for offline navigation

export async function prefetchMapsForOffline(vehicleId, bbox) {
  /**
   * Download map tiles & road network for offline use.
   */
  const { minLat, maxLat, minLon, maxLon } = bbox;

  // 1. Download map tiles (z=8-16)
  const tiles = [];
  for (let z = 8; z <= 16; z++) {
    const tileIndices = getTileIndices(minLat, maxLat, minLon, maxLon, z);
    for (const { x, y } of tileIndices) {
      const url = `https://tile.openstreetmap.org/${z}/${x}/${y}.png`;
      const response = await fetch(url);
      const blob = await response.blob();
      tiles.push({ z, x, y, blob });
    }
  }

  // 2. Store in IndexedDB
  const db = await openIndexedDB('offline-maps');
  const tx = db.transaction('tiles', 'readwrite');
  const store = tx.objectStore('tiles');

  tiles.forEach(tile => {
    store.put({
      key: `${tile.z}/${tile.x}/${tile.y}`,
      blob: tile.blob,
      timestamp: Date.now(),
    });
  });

  await tx.complete;

  // 3. Download route cache (recent routes for this vehicle)
  const routeCache = await fetch(`/api/v2/vehicles/${vehicleId}/route-cache`).then(r => r.json());
  await db.transaction('routes', 'readwrite').objectStore('routes').put({
    vehicleId,
    routes: routeCache,
    timestamp: Date.now(),
  });

  console.log(`Downloaded ${tiles.length} map tiles and ${routeCache.length} routes for offline use`);
}

export async function getOfflineRoute(vehicleId, origin, destination) {
  /**
   * Compute route using offline road network (simplified).
   */
  const db = await openIndexedDB('offline-maps');
  const routeCache = await db.objectStore('routes').get(vehicleId);

  // Check if this route exists in cache
  const cachedRoute = routeCache?.routes?.find(r =>
    distanceBetween(r.origin, origin) < 0.1 &&
    distanceBetween(r.destination, destination) < 0.1
  );

  if (cachedRoute) {
    return cachedRoute;
  }

  // Fallback: Use simplified offline algorithm (not optimal, but works)
  return {
    polyline: directLineWithoutObstacles(origin, destination),
    distance_km: distanceBetween(origin, destination) * 111, // Approximate
    duration_seconds: (distanceBetween(origin, destination) * 111 / 80) * 3600, // Assume 80 km/h avg
    notice: 'Offline mode: simplified route, not optimal',
  };
}

function getTileIndices(minLat, maxLat, minLon, maxLon, z) {
  /**
   * Convert lat/lon bbox to tile indices at zoom level z.
   */
  const tiles = [];
  const maxTile = Math.pow(2, z);

  for (let lat = minLat; lat < maxLat; lat += 1) {
    for (let lon = minLon; lon < maxLon; lon += 1) {
      const x = Math.floor(((lon + 180) / 360) * maxTile);
      const y = Math.floor(((90 - lat) / 180) * maxTile);
      tiles.push({ x, y });
    }
  }

  return tiles;
}

function distanceBetween(latLon1, latLon2) {
  /**
   * Haversine distance in km.
   */
  const [lat1, lon1] = latLon1;
  const [lat2, lon2] = latLon2;
  const R = 6371; // Earth radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.asin(Math.sqrt(a));
  return R * c;
}

async function openIndexedDB(dbName) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(dbName, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      db.createObjectStore('tiles', { keyPath: 'key' });
      db.createObjectStore('routes', { keyPath: 'vehicleId' });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
```

---

## 7. Scalability & Performance

### 7.1 Caching Strategy

```
Multi-Level Cache:

┌─────────────────────────────────────────────────────────┐
│ Level 1: Browser Cache (IndexedDB + localStorage)       │
│ - Recent routes (24h)                                   │
│ - Map tiles (pre-downloaded)                            │
│ - TTL: 24 hours                                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Level 2: CDN Cache (Cloudflare / AWS CloudFront)        │
│ - Static map tiles (XYZ)                                │
│ - Vector tiles (Mapbox GL)                              │
│ - TTL: 7 days                                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Level 3: Redis (In-Memory Cache)                        │
│ - Route cache (origin → dest): TTL 1 hour               │
│ - Traffic data: TTL 5 min (hot-update)                  │
│ - Hazard clusters: TTL 12 hours                         │
│ - Map-matched segments: TTL 24 hours                    │
│ - Vehicle state snapshots: TTL 30 seconds               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Level 4: Database (TimescaleDB + PostGIS)               │
│ - Historical GPS (30-day retention)                     │
│ - Completed routes (6-month retention)                  │
│ - Traffic events (7-day retention)                      │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Horizontal Scaling Architecture

```
                    ┌─────────────────────┐
                    │  Load Balancer      │
                    │ (Kong + Nginx)      │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
    ┌───▼────┐          ┌─────▼──┐           ┌───▼────┐
    │ API    │          │ API    │           │ API    │
    │ Pod 1  │          │ Pod 2  │    ...    │ Pod N  │
    └───┬────┘          └────┬───┘           └───┬────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼────────┐   ┌──────▼──────┐   ┌────▼──────┐
    │ Route Svc  │   │ Trail Svc   │   │ Hazard    │
    │ Replicas   │   │ (3 pods)    │   │ Svc (2)   │
    │ (5 pods)   │   │             │   │           │
    └────┬───────┘   └──────┬──────┘   └────┬──────┘
         │                  │               │
         └──────────────────┼───────────────┘
                            │
                   ┌────────▼────────┐
                   │ Kafka Cluster   │
                   │ (3-5 brokers)   │
                   └────────┬────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
┌───▼──────┐         ┌─────▼────┐         ┌───▼──────┐
│ TimescaleDB      │ Redis Cluster    │ PostGIS   │
│ (3 node)        │ (Sentinel mode)  │ (3 node)  │
└──────────┘       └──────────────────┘ └───────────┘
```

**Auto-Scaling Rules:**
- Route Service: Scale to 5-10 pods when avg response time > 500ms
- Trail Service: Scale based on GPS ingest rate (target: 100k points/sec per pod)
- Hazard Service: CPU-based scaling (target: 60% avg CPU)

### 7.3 Performance Targets

| Operation | Target Latency | SLA |
|-----------|-----------------|-----|
| Route calculation (origin/dest) | < 200 ms | 99.95% |
| GPS ingest (100k points/sec) | < 10 ms | 99.9% |
| Trail retrieval (snapped polyline) | < 100 ms | 99.95% |
| Hazard query (bbox) | < 150 ms | 99.9% |
| Map tile fetch (CDN) | < 50 ms | 99.99% |
| Real-time traffic update (WebSocket push) | < 100 ms | 99.9% |

### 7.4 Monitoring & Alerting (Prometheus + Grafana)

```yaml
# prometheus.yml alerts

groups:
  - name: fleet_routing
    rules:
      - alert: RouteLatencyHigh
        expr: histogram_quantile(0.95, rate(route_calculation_duration_ms[5m])) > 500
        for: 5m
        annotations:
          summary: "Route calculation latency > 500ms"
          
      - alert: GPSIngestBacklog
        expr: kafka_topic_partition_lag{topic="gps.raw"} > 10000
        for: 2m
        annotations:
          summary: "GPS ingest backlog > 10k points"
          
      - alert: TrailServiceDown
        expr: up{job="trail-service"} == 0
        for: 1m
        annotations:
          summary: "Trail service is down"
```

---

## 8. Reliability & Security

### 8.1 Authentication & Authorization

```python
# JWT-based auth with role-based access control

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthCredentialsDetails
import jwt
from datetime import datetime, timedelta

ALGORITHMS = ["HS256"]
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentialsDetails = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHMS)
        fleet_id = payload.get("fleet_id")
        roles = payload.get("roles", [])
        
        if not fleet_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {"fleet_id": fleet_id, "roles": roles}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(required_role: str):
    async def check_role(current_user = Depends(verify_token)):
        if required_role not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return check_role

@app.post("/api/v2/routes/calculate")
async def calculate_route(
    request: RouteRequest,
    current_user = Depends(verify_token)
):
    """Only authenticated users can calculate routes."""
    fleet_id = current_user["fleet_id"]
    # Verify vehicle belongs to fleet
    vehicle = await db.get_vehicle(request.vehicle_id)
    if vehicle.fleet_id != fleet_id:
        raise HTTPException(status_code=403, detail="Vehicle not in your fleet")
    ...

@app.get("/api/v2/vehicles/{vehicle_id}/detailed-trail")
async def get_detailed_trail(
    vehicle_id: str,
    current_user = Depends(require_role("fleet_manager"))  # Only managers can download detailed trails
):
    ...
```

### 8.2 Rate Limiting & DOS Protection

```python
# Per-user and per-IP rate limiting

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v2/routes/calculate")
@limiter.limit("100/minute")  # 100 calls per minute per IP
async def calculate_route(request: RouteRequest):
    ...

# Fleet-wide quota (e.g., free tier = 1000 routes/day)
@app.post("/api/v2/gps")
@limiter.limit("500/minute")  # 500 batches per minute per user
async def ingest_gps(
    request: GPSBatch,
    current_user = Depends(verify_token)
):
    fleet_id = current_user["fleet_id"]
    daily_usage = await redis.incr(f"gps-ingest:{fleet_id}:{date.today()}")
    
    if daily_usage > PLAN_LIMITS[fleet_id]["gps_points_per_day"]:
        raise HTTPException(status_code=429, detail="Daily quota exceeded")
    ...
```

### 8.3 Data Encryption & Privacy

```python
# Encryption at rest & in transit

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Store sensitive GPS data encrypted
from cryptography.fernet import Fernet

cipher = Fernet(ENCRYPTION_KEY)

def encrypt_gps_trace(polyline_coords):
    """Encrypt before storing in DB."""
    serialized = json.dumps(polyline_coords).encode()
    encrypted = cipher.encrypt(serialized)
    return encrypted

def decrypt_gps_trace(encrypted_data):
    decrypted = cipher.decrypt(encrypted_data)
    return json.loads(decrypted)

# GDPR data retention
@app.delete("/api/v2/gps/{vehicle_id}")
@limiter.limit("10/day")
async def delete_gps_history(
    vehicle_id: str,
    retention_days: int = 30,
    current_user = Depends(verify_token)
):
    """
    Delete GPS history older than retention_days.
    Supports GDPR "right to be forgotten".
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    await db.query("""
        DELETE FROM gps_points
        WHERE vehicle_id = %s AND time < %s
    """, [vehicle_id, cutoff_date])
    
    # Soft-delete trails (mark as anonymized)
    await db.query("""
        UPDATE trail_polylines
        SET anonymized = true, geom = ST_StartPoint(geom)
        WHERE vehicle_id = %s AND start_time < %s
    """, [vehicle_id, cutoff_date])
    
    return {"deleted_records": count, "message": f"GPS history for {vehicle_id} deleted"}
```

### 8.4 Data Backup & Disaster Recovery

```yaml
# Disaster recovery plan

backup_strategy:
  timescaledb:
    type: "continuous_archive"
    frequency: "every 6 hours"
    retention: "30 days"
    target: "s3://backup-fleet-timescaledb/"
    
  postgresql_postgis:
    type: "full_backup"
    frequency: "daily"
    retention: "90 days"
    incremental: "hourly"
    
  redis:
    type: "RDB_snapshot"
    frequency: "every 30 minutes"
    aof: "enabled"
    replication: "3_node_sentinel"

rto: "1 hour"  # Recovery Time Objective
rpo: "15 minutes"  # Recovery Point Objective

failover_procedures:
  - Automatic promotion of replicas
  - DNS failover (weighted routing)
  - Manual intervention if > 2 nodes down
```

---

## 9. Comparison vs Google Maps

| Feature | Google Maps Directions | Our Smart Routing | Advantage |
|---------|----------------------|-------------------|-----------|
| **Route Profiles** | 3 (fastest, eco, avoid highways) | 6+ (fastest, fuel, hazards, multi-modal) | **Ours**: Specialized for fleet (fuel optimization) |
| **Truck Profiles** | Limited (height/weight only) | Full profile (height, weight, hazmat, tanker) | **Ours**: Comprehensive vehicle constraints |
| **Real-Time Traffic** | Yes (incident-based) | Yes (continuous + ML prediction) | **Ours**: Predicts congestion 30 min ahead |
| **Hazard Detection** | No | Yes (AI-driven: curves, grades, schools, rail) | **Ours**: Proactive safety |
| **Map-Matching** | No (raw GPS) | Yes (snapped to roads, 95%+ confidence) | **Ours**: Historical trail accuracy |
| **Fuel Optimization** | No (generic eco mode) | Yes (vehicle weight, cargo, grade, weather) | **Ours**: Specialized algorithm |
| **SLA Monitoring** | No | Yes (geofence breaches, automated alerts) | **Ours**: Logistics-specific |
| **Multi-Modal Routing** | Limited | Yes (truck + rail + ferry) | **Ours**: Suggests load-shifting |
| **Offline Navigation** | Requires premium subscription | Built-in (free tiles + cached road network) | **Ours**: Always available |
| **Voice Guidance** | Generic | Contextual (hazard warnings, speed alerts) | **Ours**: Safety-focused |
| **API Rate Limits** | 25k/day (free) | Unlimited (enterprise) | **Ours**: Supports 1000s of vehicles |
| **Pricing** | $5-50k/month (scale) | Custom (self-hosted option available) | **Ours**: Cost-effective at scale |
| **Data Privacy** | Google collects all data | GDPR-compliant, on-prem option | **Ours**: Full data control |

---

## 10. Implementation Roadmap

### Phase 1: MVP (Weeks 1-6)
- [ ] Deploy Valhalla routing engine (OSRM fallback)
- [ ] Build Route Calculation API (`GET /routes/calculate`)
- [ ] Build GPS Ingest API (`POST /gps`)
- [ ] Implement basic map-matching (Valhalla API)
- [ ] React Leaflet UI for route visualization
- [ ] Redis caching layer
- [ ] Basic traffic integration (static HERE/TomTom feed)
- [ ] **Deliverable**: Core routing + trail display

### Phase 2: Real-Time & Hazards (Weeks 7-12)
- [ ] Kafka setup for event streaming
- [ ] Real-time traffic WebSocket subscription
- [ ] Hazard detection ML model training (OpenStreetMap + GPS data)
- [ ] Hazard API (`GET /hazards`)
- [ ] Re-routing engine (monitor + auto-adjust)
- [ ] Geofence + SLA monitoring
- [ ] **Deliverable**: Live traffic awareness + hazard alerts

### Phase 3: Optimization & Scale (Weeks 13-18)
- [ ] Fuel optimization model (calibrate with fleet data)
- [ ] Multi-modal routing (truck + rail)
- [ ] Voice guidance (WebRTC TTS)
- [ ] Offline map tile downloads
- [ ] Performance tuning (sub-200ms route queries)
- [ ] Kubernetes deployment
- [ ] **Deliverable**: Production-grade system (10k+ vehicles)

### Phase 4: Advanced Features (Weeks 19-24)
- [ ] Collaborative traffic smoothing (redistribute deliveries)
- [ ] Predictive maintenance (detect harsh driving patterns)
- [ ] Driver behavior scoring
- [ ] AI dispatch assistant (suggest best vehicle for job)
- [ ] Analytics dashboard
- [ ] **Deliverable**: Intelligent logistics platform

---

## Summary

This **Smart Routing & Trail System** exceeds Google Maps for fleet operations by:

1. **Specialized Vehicle Constraints** – Trucks have unique needs (weight, height, hazmat).
2. **Fuel Optimization** – Combines elevation, weight, and traffic to minimize consumption.
3. **Proactive Hazard Detection** – AI identifies dangerous road sections before drivers encounter them.
4. **SLA Compliance** – Real-time monitoring with automated breach alerts.
5. **Offline Capability** – Pre-downloaded maps + cached routes work without internet.
6. **Enterprise Privacy** – Full data control; GDPR-compliant; self-hosted option.
7. **Scalable Infrastructure** – Serves 10k+ vehicles with sub-200ms latency.
8. **Real-Time Resilience** – Continuous re-routing adapts to traffic, accidents, and weather.

**Start with Phase 1 (MVP)** to validate the core routing + trail features, then layer in real-time traffic (Phase 2) and advanced optimizations (Phases 3–4).
