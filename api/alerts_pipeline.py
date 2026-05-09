"""
Production-grade alert evaluation pipeline with bounded queue, prefiltering, 
and robust geometry handling. Prevents crashes and ensures low-latency processing.
"""
import logging
import time
import json
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Tuple
from threading import Lock, Thread, Event
from queue import Queue, Full
import traceback
import math

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG AND METRICS
# ============================================================================

class AlertConfig:
    """Tunable parameters for alert evaluation"""
    def __init__(self):
        # Off-route detection
        self.off_route_consensus_count = 3  # N consecutive points
        self.off_route_window_seconds = 30  # Sliding window
        self.off_route_distance_threshold_m = 50  # Meters from polyline
        
        # Rate limiting and queueing
        self.max_queue_size = 10000
        self.max_events_per_device_per_sec = 10
        self.worker_threads = 4
        
        # Backoff for repeated alerts
        self.alert_cooldown_seconds = 300  # 5 min default
        self.cooldown_multiplier = 2.0  # Exponential backoff
        
        # Sampling under load
        self.sampling_rate_degraded = 0.5  # Sample 50% if queue > 80%
        self.queue_high_watermark = 0.8

class AlertMetrics:
    """Metrics collection for monitoring"""
    def __init__(self):
        self.queue_length = 0
        self.dropped_events = 0
        self.processed_events = 0
        self.alert_latencies = deque(maxlen=1000)  # Last 1000 for p50/p95
        self.exceptions = 0
        self.off_route_alerts = 0
        self.false_positive_suppressions = 0
        self._lock = Lock()
    
    def record_latency(self, latency_ms: float):
        with self._lock:
            self.alert_latencies.append(latency_ms)
    
    def record_exception(self):
        with self._lock:
            self.exceptions += 1
    
    def get_percentiles(self) -> Dict[str, float]:
        with self._lock:
            if not self.alert_latencies:
                return {'p50': 0, 'p95': 0}
            sorted_lat = sorted(self.alert_latencies)
            p50_idx = len(sorted_lat) // 2
            p95_idx = int(len(sorted_lat) * 0.95)
            return {
                'p50': sorted_lat[p50_idx],
                'p95': sorted_lat[p95_idx] if p95_idx < len(sorted_lat) else sorted_lat[-1]
            }

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class LocationPoint:
    """Immutable telemetry point"""
    truck_id: str
    latitude: float
    longitude: float
    speed_kmh: float
    timestamp: datetime
    trace_id: str
    
    def to_dict(self):
        return {
            'truck_id': self.truck_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'speed_kmh': self.speed_kmh,
            'timestamp': self.timestamp.isoformat(),
            'trace_id': self.trace_id
        }

@dataclass
class RoutePolyline:
    """Immutable route definition"""
    route_id: str
    points: List[Tuple[float, float]]  # [(lat, lng), ...]
    
    def is_valid(self) -> bool:
        """Validate route has at least 2 points"""
        return bool(self.points) and len(self.points) >= 2

@dataclass
class AlertDecision:
    """Result of alert evaluation"""
    truck_id: str
    alert_type: str  # 'off_route', 'speeding', etc.
    severity: str  # 'warning', 'critical'
    message: str
    distance_from_route_m: Optional[float]
    trace_id: str
    created_at: datetime
    
    def to_dict(self):
        return {
            'truck_id': self.truck_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'distance_from_route_m': self.distance_from_route_m,
            'trace_id': self.trace_id,
            'created_at': self.created_at.isoformat()
        }

@dataclass
class EvaluationContext:
    """Context for alert evaluation with replay capability"""
    location: LocationPoint
    route: Optional[RoutePolyline]
    previous_location: Optional[LocationPoint]
    truck_state: Dict  # truck status, heading, etc.
    
    def to_replay_log(self):
        return {
            'location': self.location.to_dict(),
            'route': {'route_id': self.route.route_id, 'point_count': len(self.route.points)} if self.route else None,
            'truck_state': self.truck_state,
            'timestamp': datetime.utcnow().isoformat()
        }

# ============================================================================
# GEOMETRY UTILITIES (DEFENSIVE)
# ============================================================================

class GeometryUtils:
    """Robust geometry calculations with fallbacks"""
    
    EARTH_RADIUS_M = 6371000  # meters
    
    @staticmethod
    def haversine_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate distance between two lat/lng points in meters"""
        try:
            lat1, lng1 = p1
            lat2, lng2 = p2
            
            if not all(isinstance(x, (int, float)) for x in [lat1, lng1, lat2, lng2]):
                logger.warning(f"Invalid coordinate types: {p1}, {p2}")
                return float('inf')
            
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))
            
            return GeometryUtils.EARTH_RADIUS_M * c
        except Exception as e:
            logger.error(f"Haversine calc error: {e}")
            return float('inf')
    
    @staticmethod
    def bounding_box_distance(point: Tuple[float, float], 
                             polyline: List[Tuple[float, float]]) -> float:
        """Fast bounding box check as prefilter"""
        try:
            if not polyline or len(polyline) < 2:
                return float('inf')
            
            lats = [p[0] for p in polyline]
            lngs = [p[1] for p in polyline]
            
            min_lat, max_lat = min(lats), max(lats)
            min_lng, max_lng = min(lngs), max(lngs)
            
            # Add 10% buffer
            lat_buffer = (max_lat - min_lat) * 0.1 + 0.01
            lng_buffer = (max_lng - min_lng) * 0.1 + 0.01
            
            if (min_lat - lat_buffer <= point[0] <= max_lat + lat_buffer and
                min_lng - lng_buffer <= point[1] <= max_lng + lng_buffer):
                return 0  # Inside bounding box (cheap check)
            
            return float('inf')  # Outside bounding box
        except Exception as e:
            logger.error(f"Bounding box error: {e}")
            return float('inf')
    
    @staticmethod
    def point_to_polyline_distance(point: Tuple[float, float], 
                                  polyline: List[Tuple[float, float]]) -> float:
        """Distance from point to nearest segment in polyline"""
        try:
            if not polyline or len(polyline) < 2:
                logger.warning("Invalid polyline for distance calc")
                return float('inf')
            
            min_distance = float('inf')
            
            for i in range(len(polyline) - 1):
                seg_start = polyline[i]
                seg_end = polyline[i + 1]
                dist = GeometryUtils._point_to_segment_distance(point, seg_start, seg_end)
                min_distance = min(min_distance, dist)
            
            return min_distance
        except Exception as e:
            logger.error(f"Polyline distance error: {e}, traceback: {traceback.format_exc()}")
            return float('inf')
    
    @staticmethod
    def _point_to_segment_distance(point: Tuple[float, float], 
                                   seg_start: Tuple[float, float], 
                                   seg_end: Tuple[float, float]) -> float:
        """Distance from point to line segment using projection"""
        try:
            # Convert to meters for calculation (simplified: assume ~111km per degree)
            lat_to_m = 111000
            lng_to_m = 111000 * math.cos(math.radians(point[0]))
            
            px = (point[1] - seg_start[1]) * lng_to_m
            py = (point[0] - seg_start[0]) * lat_to_m
            
            dx = (seg_end[1] - seg_start[1]) * lng_to_m
            dy = (seg_end[0] - seg_start[0]) * lat_to_m
            
            if dx == 0 and dy == 0:
                return GeometryUtils.haversine_distance(point, seg_start)
            
            t = max(0, min(1, (px * dx + py * dy) / (dx * dx + dy * dy)))
            
            closest_x = seg_start[1] * lng_to_m + t * dx
            closest_y = seg_start[0] * lat_to_m + t * dy
            
            dist = math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)
            return dist
        except Exception as e:
            logger.error(f"Segment distance error: {e}")
            return float('inf')

# ============================================================================
# PREFILTER (CHEAP CHECKS)
# ============================================================================

class LocationPrefilter:
    """Lightweight prefilter to reject obviously invalid points"""
    
    @staticmethod
    def validate_and_prefilter(context: EvaluationContext) -> Tuple[bool, Optional[str]]:
        """
        Returns (should_process, reject_reason)
        """
        loc = context.location
        
        # Check coordinate ranges
        if not (-90 <= loc.latitude <= 90 and -180 <= loc.longitude <= 180):
            return False, "invalid_coordinates"
        
        # Check timestamp freshness (not older than 5 minutes)
        age_sec = (datetime.utcnow() - loc.timestamp).total_seconds()
        if age_sec > 300:
            return False, "stale_timestamp"
        
        # Speed sanity check (>300 km/h is unrealistic for truck)
        if loc.speed_kmh > 300:
            return False, "unrealistic_speed"
        
        # Route must exist for off-route checks
        if context.route and not context.route.is_valid():
            return False, "invalid_route"
        
        return True, None

# ============================================================================
# ALERT EVALUATION ENGINE
# ============================================================================

class AlertEvaluator:
    """Core alert evaluation with defensive geometry"""
    
    def __init__(self, config: AlertConfig, metrics: AlertMetrics):
        self.config = config
        self.metrics = metrics
        self.vehicle_states = {}  # truck_id -> {last_off_route_time, consecutive_out_of_route, etc.}
        self._lock = Lock()
    
    def evaluate(self, context: EvaluationContext) -> List[AlertDecision]:
        """
        Evaluate single telemetry point and return any alerts.
        Protected with try/catch to prevent crashes.
        """
        alerts = []
        start_time = time.time()
        
        try:
            # Prefilter
            is_valid, reject_reason = LocationPrefilter.validate_and_prefilter(context)
            if not is_valid:
                logger.debug(f"Point rejected: {reject_reason} for {context.location.truck_id}")
                return alerts
            
            # Off-route alert
            off_route_alert = self._check_off_route(context)
            if off_route_alert:
                alerts.append(off_route_alert)
                self.metrics.off_route_alerts += 1
            
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record_latency(latency_ms)
            self.metrics.processed_events += 1
            
        except Exception as e:
            logger.error(f"Alert evaluation error: {e}, traceback: {traceback.format_exc()}")
            self.metrics.record_exception()
            # Swallow exception—do not crash the pipeline
        
        return alerts
    
    def _check_off_route(self, context: EvaluationContext) -> Optional[AlertDecision]:
        """
        Off-route detection with N-consecutive consensus and exponential backoff.
        """
        if not context.route or not context.route.is_valid():
            return None
        
        loc = context.location
        truck_id = loc.truck_id
        
        # Get or initialize vehicle state
        with self._lock:
            if truck_id not in self.vehicle_states:
                self.vehicle_states[truck_id] = {
                    'consecutive_out_of_route': 0,
                    'last_alert_time': None,
                    'alert_cooldown_sec': self.config.alert_cooldown_seconds
                }
            state = self.vehicle_states[truck_id]
        
        # Check if on cooldown
        if state['last_alert_time']:
            time_since_alert = (datetime.utcnow() - state['last_alert_time']).total_seconds()
            if time_since_alert < state['alert_cooldown_sec']:
                self.metrics.false_positive_suppressions += 1
                return None
        
        # Calculate distance from route
        distance_m = GeometryUtils.point_to_polyline_distance(
            (loc.latitude, loc.longitude),
            context.route.points
        )
        
        if distance_m == float('inf'):
            logger.warning(f"Could not compute distance for {truck_id}")
            return None
        
        # Update consensus counter
        if distance_m > self.config.off_route_distance_threshold_m:
            state['consecutive_out_of_route'] += 1
        else:
            state['consecutive_out_of_route'] = 0
        
        # Trigger alert after N consecutive points
        if state['consecutive_out_of_route'] >= self.config.off_route_consensus_count:
            alert = AlertDecision(
                truck_id=truck_id,
                alert_type='off_route',
                severity='warning',
                message=f"Truck {truck_id} deviated {distance_m:.1f}m from planned route",
                distance_from_route_m=distance_m,
                trace_id=loc.trace_id,
                created_at=datetime.utcnow()
            )
            
            # Update cooldown with exponential backoff
            with self._lock:
                state['last_alert_time'] = datetime.utcnow()
                state['alert_cooldown_sec'] = min(
                    self.config.alert_cooldown_seconds * (self.config.cooldown_multiplier ** 
                                                          (state.get('alert_count', 0))),
                    3600  # Cap at 1 hour
                )
                state['alert_count'] = state.get('alert_count', 0) + 1
                state['consecutive_out_of_route'] = 0  # Reset counter after alert
            
            return alert
        
        return None

# ============================================================================
# BOUNDED QUEUE WITH BACKPRESSURE
# ============================================================================

class BoundedAlertQueue:
    """Bounded in-memory queue with backpressure and sampling under load"""
    
    def __init__(self, max_size: int, config: AlertConfig, metrics: AlertMetrics):
        self.queue = deque(maxlen=max_size)
        self.max_size = max_size
        self.config = config
        self.metrics = metrics
        self._lock = Lock()
    
    def try_enqueue(self, context: EvaluationContext) -> bool:
        """Try to enqueue; apply sampling if queue is high"""
        with self._lock:
            queue_usage = len(self.queue) / self.max_size
            
            # Under high load, sample points
            if queue_usage > self.config.queue_high_watermark:
                if context.location.timestamp.timestamp() % 10 != 0:  # Simple hash-based sampling
                    self.metrics.dropped_events += 1
                    logger.warning(f"Dropping point due to queue backpressure: {queue_usage:.1%}")
                    return False
            
            try:
                self.queue.append(context)
                self.metrics.queue_length = len(self.queue)
                return True
            except:
                self.metrics.dropped_events += 1
                return False
    
    def dequeue_batch(self, batch_size: int) -> List[EvaluationContext]:
        """Dequeue up to batch_size items"""
        with self._lock:
            batch = []
            for _ in range(min(batch_size, len(self.queue))):
                if self.queue:
                    batch.append(self.queue.popleft())
            self.metrics.queue_length = len(self.queue)
            return batch

# ============================================================================
# WORKER POOL
# ============================================================================

class AlertWorker(Thread):
    """Background worker thread for alert evaluation"""
    
    def __init__(self, queue: BoundedAlertQueue, evaluator: AlertEvaluator,
                 stop_event: Event, batch_size: int = 100):
        super().__init__(daemon=True)
        self.queue = queue
        self.evaluator = evaluator
        self.stop_event = stop_event
        self.batch_size = batch_size
    
    def run(self):
        """Worker main loop"""
        logger.info("Alert worker started")
        while not self.stop_event.is_set():
            batch = self.queue.dequeue_batch(self.batch_size)
            if batch:
                for context in batch:
                    alerts = self.evaluator.evaluate(context)
                    for alert in alerts:
                        # TODO: persist alert to database and notify
                        logger.info(f"Alert: {alert.to_dict()}")
            else:
                time.sleep(0.1)
        logger.info("Alert worker stopped")

# ============================================================================
# PIPELINE ORCHESTRATOR
# ============================================================================

class AlertPipeline:
    """Main alert pipeline orchestrator"""
    
    def __init__(self, config: AlertConfig = None):
        self.config = config or AlertConfig()
        self.metrics = AlertMetrics()
        self.queue = BoundedAlertQueue(self.config.max_queue_size, self.config, self.metrics)
        self.evaluator = AlertEvaluator(self.config, self.metrics)
        self.stop_event = Event()
        self.workers = []
        self._start_workers()
    
    def _start_workers(self):
        """Start background worker threads"""
        for i in range(self.config.worker_threads):
            worker = AlertWorker(self.queue, self.evaluator, self.stop_event)
            worker.start()
            self.workers.append(worker)
        logger.info(f"Started {len(self.workers)} alert workers")
    
    def ingest_location(self, location: LocationPoint, route: Optional[RoutePolyline] = None,
                       truck_state: Dict = None) -> bool:
        """
        Ingest a location point into the pipeline.
        Returns True if queued, False if dropped due to backpressure.
        """
        context = EvaluationContext(
            location=location,
            route=route,
            previous_location=None,
            truck_state=truck_state or {}
        )
        return self.queue.try_enqueue(context)
    
    def get_metrics(self) -> Dict:
        """Get current pipeline metrics"""
        percentiles = self.metrics.get_percentiles()
        return {
            'queue_length': self.metrics.queue_length,
            'dropped_events': self.metrics.dropped_events,
            'processed_events': self.metrics.processed_events,
            'exceptions': self.metrics.exceptions,
            'off_route_alerts': self.metrics.off_route_alerts,
            'false_positive_suppressions': self.metrics.false_positive_suppressions,
            'alert_latency_p50_ms': percentiles['p50'],
            'alert_latency_p95_ms': percentiles['p95']
        }
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down alert pipeline")
        self.stop_event.set()
        for worker in self.workers:
            worker.join(timeout=5)
        logger.info("Alert pipeline shut down")
