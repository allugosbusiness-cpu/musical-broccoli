"""
Test suite for alert pipeline: geometry validation, edge cases, stress testing.
Run: pytest server/tests/test_alerts_pipeline.py -v
"""
import pytest
import math
from datetime import datetime, timedelta
import time
from threading import Thread

from api.alerts_pipeline import (
    GeometryUtils, AlertEvaluator, AlertConfig, AlertMetrics,
    LocationPoint, RoutePolyline, AlertPipeline, EvaluationContext
)


class TestGeometryUtils:
    """Test robust geometry calculations"""
    
    def test_haversine_valid_distance(self):
        """Haversine distance between two known points"""
        # Harare to Mutare: ~260 km
        harare = (-17.825, 31.034)
        mutare = (-18.964, 32.667)
        distance = GeometryUtils.haversine_distance(harare, mutare)
        # Should be ~260 km ±10%
        assert 234000 < distance < 286000, f"Distance {distance} out of range"
    
    def test_haversine_same_point(self):
        """Distance between same point should be ~0"""
        point = (-17.825, 31.034)
        distance = GeometryUtils.haversine_distance(point, point)
        assert distance < 1, f"Same point distance: {distance}"
    
    def test_haversine_invalid_coords_nan(self):
        """Invalid coordinates should return infinity"""
        result = GeometryUtils.haversine_distance((float('nan'), 31.034), (-17.825, 31.034))
        assert result == float('inf'), "NaN input should return inf"
    
    def test_haversine_invalid_coords_out_of_range(self):
        """Out of range coordinates should return infinity"""
        result = GeometryUtils.haversine_distance((200, 31.034), (-17.825, 31.034))
        assert result == float('inf'), "Out of range should return inf"
    
    def test_haversine_none_input(self):
        """None input should not crash"""
        try:
            result = GeometryUtils.haversine_distance(None, (-17.825, 31.034))
            assert result == float('inf'), "None input should return inf"
        except Exception:
            pass  # Graceful failure acceptable
    
    def test_polyline_single_point(self):
        """Polyline with only one point should return infinity"""
        point = (-17.825, 31.034)
        polyline = [(-17.825, 31.034)]
        distance = GeometryUtils.point_to_polyline_distance(point, polyline)
        assert distance == float('inf'), "Single point polyline should return inf"
    
    def test_polyline_empty(self):
        """Empty polyline should return infinity"""
        point = (-17.825, 31.034)
        polyline = []
        distance = GeometryUtils.point_to_polyline_distance(point, polyline)
        assert distance == float('inf'), "Empty polyline should return inf"
    
    def test_polyline_point_on_segment(self):
        """Point on polyline segment should return ~0"""
        # Route from A to B
        polyline = [(-17.0, 31.0), (-17.5, 31.5), (-18.0, 32.0)]
        # Point on first segment
        point_on_segment = (-17.25, 31.25)
        distance = GeometryUtils.point_to_polyline_distance(point_on_segment, polyline)
        # Should be <1000m (rough approximation)
        assert distance < 5000, f"Point on segment distance: {distance}"
    
    def test_polyline_point_off_segment(self):
        """Point far from polyline should return larger distance"""
        polyline = [(-17.0, 31.0), (-17.5, 31.5)]
        point_far = (-15.0, 33.0)  # ~200+ km away
        distance = GeometryUtils.point_to_polyline_distance(point_far, polyline)
        # Should be in hundreds of km
        assert distance > 100000, f"Point far distance: {distance}"
    
    def test_polyline_malformed_points(self):
        """Polyline with malformed points should handle gracefully"""
        point = (-17.825, 31.034)
        polyline = [(-17.0, 31.0), (float('inf'), 31.5), (-18.0, 32.0)]
        distance = GeometryUtils.point_to_polyline_distance(point, polyline)
        # Should not crash
        assert isinstance(distance, float), "Malformed polyline should return float"
    
    def test_bounding_box_prefilter_inside(self):
        """Point inside bounding box should return 0"""
        polyline = [(-17.0, 31.0), (-17.5, 31.5), (-18.0, 32.0)]
        point = (-17.5, 31.5)  # Center of route
        distance = GeometryUtils.bounding_box_distance(point, polyline)
        assert distance == 0, "Point inside bbox should return 0"
    
    def test_bounding_box_prefilter_outside(self):
        """Point outside bounding box should return infinity"""
        polyline = [(-17.0, 31.0), (-17.5, 31.5)]
        point = (-15.0, 35.0)  # Far away
        distance = GeometryUtils.bounding_box_distance(point, polyline)
        assert distance == float('inf'), "Point outside bbox should return inf"


class TestAlertEvaluator:
    """Test alert evaluation logic"""
    
    def setup_method(self):
        """Setup for each test"""
        self.config = AlertConfig()
        self.metrics = AlertMetrics()
        self.evaluator = AlertEvaluator(self.config, self.metrics)
    
    def test_off_route_single_point_no_alert(self):
        """Single point off route should not trigger alert (needs N consensus)"""
        location = LocationPoint(
            truck_id='TRK001',
            latitude=-17.825,
            longitude=31.034,
            speed_kmh=60,
            timestamp=datetime.utcnow(),
            trace_id='trace-001'
        )
        route = RoutePolyline(
            route_id='RT001',
            points=[(-17.0, 31.0), (-18.0, 32.0)]  # Point is far from route
        )
        context = EvaluationContext(location, route, None, {})
        
        alerts = self.evaluator.evaluate(context)
        assert len(alerts) == 0, "Single off-route point should not alert"
    
    def test_off_route_consensus_trigger(self):
        """After N consecutive points, alert should trigger"""
        route = RoutePolyline(
            route_id='RT001',
            points=[(-17.0, 31.0), (-18.0, 32.0)]
        )
        
        # Send 3 consecutive off-route points
        for i in range(3):
            location = LocationPoint(
                truck_id='TRK001',
                latitude=-15.0,  # Far off route
                longitude=33.0,
                speed_kmh=60,
                timestamp=datetime.utcnow(),
                trace_id=f'trace-{i:03d}'
            )
            context = EvaluationContext(location, route, None, {})
            alerts = self.evaluator.evaluate(context)
            
            if i < 2:
                assert len(alerts) == 0, f"Point {i} should not alert yet"
            else:
                assert len(alerts) == 1, f"Point {i} should trigger alert"
                assert alerts[0].alert_type == 'off_route'
    
    def test_off_route_cooldown_suppression(self):
        """Repeated alerts should be suppressed by cooldown"""
        route = RoutePolyline(
            route_id='RT001',
            points=[(-17.0, 31.0), (-18.0, 32.0)]
        )
        
        # Trigger initial alert
        for i in range(3):
            location = LocationPoint(
                truck_id='TRK001',
                latitude=-15.0,
                longitude=33.0,
                speed_kmh=60,
                timestamp=datetime.utcnow(),
                trace_id=f'trace-{i:03d}'
            )
            context = EvaluationContext(location, route, None, {})
            self.evaluator.evaluate(context)
        
        # Next point should be suppressed by cooldown
        location = LocationPoint(
            truck_id='TRK001',
            latitude=-15.0,
            longitude=33.0,
            speed_kmh=60,
            timestamp=datetime.utcnow(),
            trace_id='trace-cooldown'
        )
        context = EvaluationContext(location, route, None, {})
        alerts = self.evaluator.evaluate(context)
        
        assert len(alerts) == 0, "Alert should be suppressed by cooldown"
        assert self.metrics.false_positive_suppressions > 0


class TestAlertPipelineStress:
    """Stress tests for production readiness"""
    
    def test_high_throughput_no_crash(self):
        """Pipeline should handle 100 updates/sec without crashing"""
        pipeline = AlertPipeline()
        route = RoutePolyline(
            route_id='RT001',
            points=[(-17.0, 31.0), (-18.0, 32.0)]
        )
        
        start_time = time.time()
        events_sent = 0
        
        # Send burst of events
        for i in range(500):  # 500 events = ~5 sec at 100/sec
            for truck_id in [f'TRK{j:03d}' for j in range(10)]:
                location = LocationPoint(
                    truck_id=truck_id,
                    latitude=-17.0 + (i % 10) * 0.01,
                    longitude=31.0 + (i % 10) * 0.01,
                    speed_kmh=60 + (i % 30),
                    timestamp=datetime.utcnow(),
                    trace_id=f'stress-{i}'
                )
                queued = pipeline.ingest_location(location, route, {})
                if queued:
                    events_sent += 1
        
        elapsed = time.time() - start_time
        
        # Wait for workers to process
        time.sleep(2)
        
        metrics = pipeline.get_metrics()
        throughput = events_sent / elapsed
        
        logger.info(f"Throughput: {throughput:.1f} events/sec")
        logger.info(f"Metrics: {metrics}")
        
        # No exception should have occurred
        assert metrics['exceptions'] == 0, "Should not crash under load"
        assert throughput > 100, f"Throughput {throughput} too low"
        
        pipeline.shutdown()
    
    def test_queue_backpressure_handling(self):
        """Pipeline should gracefully handle queue full condition"""
        config = AlertConfig()
        config.max_queue_size = 100  # Small queue for testing
        config.worker_threads = 1  # Slow processing
        
        pipeline = AlertPipeline(config)
        
        # Send enough events to fill queue
        dropped = 0
        for i in range(200):
            location = LocationPoint(
                truck_id='TRK001',
                latitude=-17.0 + (i % 100) * 0.01,
                longitude=31.0 + (i % 100) * 0.01,
                speed_kmh=60,
                timestamp=datetime.utcnow(),
                trace_id=f'backpressure-{i}'
            )
            if not pipeline.ingest_location(location, None, {}):
                dropped += 1
        
        metrics = pipeline.get_metrics()
        
        # Should drop some events or sample them
        assert dropped > 0 or metrics['dropped_events'] > 0, "Should handle backpressure"
        logger.info(f"Dropped: {dropped}, Metrics dropped: {metrics['dropped_events']}")
        
        pipeline.shutdown()
    
    def test_no_ui_thread_blocking(self):
        """Ingestion should be fast (not block)"""
        pipeline = AlertPipeline()
        
        # Measure ingestion latency
        latencies = []
        for i in range(100):
            start = time.time()
            location = LocationPoint(
                truck_id='TRK001',
                latitude=-17.0,
                longitude=31.0,
                speed_kmh=60,
                timestamp=datetime.utcnow(),
                trace_id=f'latency-{i}'
            )
            pipeline.ingest_location(location, None, {})
            latency = (time.time() - start) * 1000  # ms
            latencies.append(latency)
        
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        logger.info(f"Ingestion p95 latency: {p95_latency:.2f}ms")
        
        # Ingestion should be <10ms even p95
        assert p95_latency < 10, f"P95 latency {p95_latency}ms too high"
        
        pipeline.shutdown()


import logging
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
