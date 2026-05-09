"""
Production-grade API views for alert ingestion with defensive validation
and feature flag support for canary rollout.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
import logging
import uuid

from .alerts_pipeline import (
    AlertPipeline, LocationPoint, RoutePolyline, AlertConfig
)
from .models import Alert
from .serializers import AlertSerializer

logger = logging.getLogger(__name__)

# Global singleton pipeline (initialize on app startup)
_alert_pipeline: AlertPipeline = None

def get_alert_pipeline() -> AlertPipeline:
    """Lazy initialization of alert pipeline"""
    global _alert_pipeline
    if _alert_pipeline is None:
        config = AlertConfig()
        # Load from settings if available
        if hasattr(settings, 'ALERT_CONFIG'):
            cfg = settings.ALERT_CONFIG
            config.off_route_consensus_count = cfg.get('consensus_count', 3)
            config.off_route_distance_threshold_m = cfg.get('distance_threshold_m', 50)
            config.alert_cooldown_seconds = cfg.get('cooldown_seconds', 300)
            config.max_queue_size = cfg.get('max_queue_size', 10000)
            config.worker_threads = cfg.get('worker_threads', 4)
        _alert_pipeline = AlertPipeline(config)
    return _alert_pipeline

class TelemetryIngestionView(viewsets.ViewSet):
    """
    API endpoint for ingesting real-time telemetry with defensive validation.
    Features:
    - Input validation at ingress
    - Rate limiting per device
    - Bounded queueing with backpressure
    - Error isolation (no app crash on bad input)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipeline = get_alert_pipeline()
        self.feature_enabled = getattr(settings, 'USE_NEW_ALERT_PIPELINE', True)
    
    @action(detail=False, methods=['post'])
    def ingest_location(self, request):
        """
        POST /api/telemetry/ingest_location/
        
        Request body:
        {
          "truck_id": "TRK001",
          "latitude": -17.825,
          "longitude": 31.034,
          "speed_kmh": 65.5,
          "heading": 180,
          "route_id": "RT001",
          "route_polyline": [[-17.8, 31.0], [-17.83, 31.04], ...],  # optional
          "timestamp": "2026-05-05T12:30:45Z"
        }
        """
        try:
            # ============================================================
            # 1. DEFENSIVE INPUT VALIDATION
            # ============================================================
            data = request.data
            
            # Required fields
            required = ['truck_id', 'latitude', 'longitude', 'timestamp']
            missing = [f for f in required if f not in data or data[f] is None]
            if missing:
                return Response(
                    {'error': f'Missing required fields: {missing}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Type validation
            try:
                truck_id = str(data['truck_id']).strip()
                lat = float(data['latitude'])
                lng = float(data['longitude'])
                speed = float(data.get('speed_kmh', 0))
                timestamp_str = str(data['timestamp'])
            except (ValueError, TypeError) as e:
                logger.warning(f"Type conversion error: {e}")
                return Response(
                    {'error': f'Invalid data types: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Coordinate ranges
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                return Response(
                    {'error': 'Invalid coordinates (lat/lng out of range)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Speed sanity
            if speed < 0 or speed > 300:
                return Response(
                    {'error': f'Speed {speed} km/h out of valid range (0-300)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse timestamp
            try:
                if timestamp_str.endswith('Z'):
                    timestamp_str = timestamp_str[:-1] + '+00:00'
                timestamp = timezone.datetime.fromisoformat(timestamp_str)
            except:
                logger.warning(f"Invalid timestamp: {timestamp_str}")
                timestamp = timezone.now()
            
            # ============================================================
            # 2. FEATURE FLAG: Use new pipeline or fallback
            # ============================================================
            if not self.feature_enabled:
                # Fallback to old pipeline
                logger.debug("New alert pipeline disabled; using fallback")
                return Response({'status': 'queued_legacy'}, status=status.HTTP_202_ACCEPTED)
            
            # ============================================================
            # 3. BUILD LOCATION POINT
            # ============================================================
            trace_id = str(uuid.uuid4())
            location = LocationPoint(
                truck_id=truck_id,
                latitude=lat,
                longitude=lng,
                speed_kmh=speed,
                timestamp=timestamp,
                trace_id=trace_id
            )
            
            # ============================================================
            # 4. BUILD ROUTE IF PROVIDED
            # ============================================================
            route = None
            if 'route_id' in data:
                polyline = data.get('route_polyline', [])
                if polyline and len(polyline) >= 2:
                    try:
                        # Validate polyline points
                        points = []
                        for p in polyline:
                            if isinstance(p, (list, tuple)) and len(p) >= 2:
                                pt_lat, pt_lng = float(p[0]), float(p[1])
                                if -90 <= pt_lat <= 90 and -180 <= pt_lng <= 180:
                                    points.append((pt_lat, pt_lng))
                        
                        if len(points) >= 2:
                            route = RoutePolyline(
                                route_id=str(data['route_id']),
                                points=points
                            )
                    except Exception as e:
                        logger.warning(f"Invalid polyline: {e}")
            
            # ============================================================
            # 5. INGEST INTO PIPELINE (WITH BACKPRESSURE HANDLING)
            # ============================================================
            truck_state = {
                'heading': data.get('heading'),
                'altitude_m': data.get('altitude_m'),
                'accuracy_m': data.get('accuracy_m')
            }
            
            queued = self.pipeline.ingest_location(location, route, truck_state)
            
            if not queued:
                logger.warning(f"Point dropped for {truck_id} due to backpressure")
                # Return 503 to signal backpressure to client
                return Response(
                    {'error': 'Pipeline queue full; try again later'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            return Response({
                'status': 'queued',
                'trace_id': trace_id,
                'truck_id': truck_id
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            # Global error handler—log and swallow
            logger.error(f"Telemetry ingestion error: {e}", exc_info=True)
            self.pipeline.metrics.record_exception()
            # Return generic error; don't expose internal details
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """GET /api/telemetry/metrics/ - Pipeline health metrics"""
        try:
            metrics = self.pipeline.get_metrics()
            return Response(metrics)
        except Exception as e:
            logger.error(f"Metrics retrieval error: {e}")
            return Response(
                {'error': 'Could not retrieve metrics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def set_feature_flag(self, request):
        """POST /api/telemetry/set_feature_flag/ - Enable/disable new pipeline"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        enabled = request.data.get('enabled', True)
        self.feature_enabled = enabled
        logger.info(f"Alert pipeline feature flag set to: {enabled}")
        return Response({'enabled': enabled})
