"""
Kafka Stream Processor for Fleet Management
Handles real-time GPS ingestion, map-matching, traffic updates, and re-routing triggers
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = ['kafka:29092']
KAFKA_TOPICS = {
    'gps.raw': 'Raw GPS points from vehicles',
    'gps.snapped': 'Map-matched (snapped) GPS points',
    'traffic.update': 'Real-time traffic events',
    'alerts.hazard': 'Hazard detection alerts',
    'route.updated': 'Route updates and changes',
    'reroute.triggered': 'Automatic re-route triggers',
    'sla.breach': 'SLA breach events',
    'analytics.metrics': 'Aggregated metrics for analytics',
}

class KafkaStreamProcessor:
    """
    Stream processor for real-time fleet data
    Coordinates GPS ingestion, map-matching, hazard detection, and re-routing
    """

    def __init__(self, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS):
        self.bootstrap_servers = bootstrap_servers
        self.producers = {}
        self.consumers = {}
        self.vehicle_buffers = defaultdict(list)  # Buffer GPS points per vehicle
        self.buffer_size = 50  # Points before flushing
        self.buffer_timeout = 10  # seconds

    def initialize(self):
        """Initialize Kafka connections and create topics if needed"""
        logger.info("Initializing Kafka Stream Processor...")
        
        # Create producer
        self.default_producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',  # Wait for all replicas
            retries=3,
            max_in_flight_requests_per_connection=1  # Maintain order
        )

        # Create topics if they don't exist
        self._create_topics()

        logger.info("✓ Kafka Stream Processor initialized")

    def _create_topics(self):
        """Create Kafka topics with proper configuration"""
        from kafka.admin import KafkaAdminClient, NewTopic
        
        admin_client = KafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            request_timeout_ms=5000
        )

        topics_to_create = []
        for topic_name, description in KAFKA_TOPICS.items():
            topics_to_create.append(NewTopic(
                name=topic_name,
                num_partitions=3,  # 3 partitions for parallelism
                replication_factor=1,  # Single cluster (adjust for multi-node)
                topic_configs={
                    'retention.ms': str(7 * 24 * 60 * 60 * 1000),  # 7 days
                    'compression.type': 'snappy',  # Reduce storage
                    'min.insync.replicas': '1'
                }
            ))

        try:
            fs = admin_client.create_topics(new_topics=topics_to_create, validate_only=False)
            for topic, f in fs.items():
                try:
                    f.result()  # Wait for operation
                    logger.info(f"✓ Topic created: {topic}")
                except Exception as e:
                    logger.debug(f"Topic {topic} already exists or error: {e}")
        except Exception as e:
            logger.error(f"Error creating topics: {e}")
        finally:
            admin_client.close()

    async def process_gps_stream(self):
        """
        Main GPS processing pipeline
        1. Consume raw GPS from gps.raw topic
        2. Buffer points per vehicle
        3. Send to map-matching service
        4. Publish snapped points to gps.snapped topic
        5. Trigger re-routing if needed
        """
        consumer = KafkaConsumer(
            'gps.raw',
            bootstrap_servers=self.bootstrap_servers,
            group_id='gps-processor',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            max_poll_records=100  # Batch process
        )

        logger.info("GPS stream processor started")

        for message in consumer:
            try:
                gps_data = message.value
                vehicle_id = gps_data.get('vehicle_id')
                
                # Buffer GPS points
                self.vehicle_buffers[vehicle_id].append(gps_data)

                # Check if buffer is ready to flush
                if len(self.vehicle_buffers[vehicle_id]) >= self.buffer_size:
                    await self._process_gps_batch(vehicle_id)

            except Exception as e:
                logger.error(f"Error processing GPS message: {e}")

    async def _process_gps_batch(self, vehicle_id: str):
        """
        Process batched GPS points through map-matching
        """
        points = self.vehicle_buffers[vehicle_id]
        
        if not points:
            return

        try:
            # In production, call map-matching service
            # snapped_points = await map_matching_service.match(points)
            
            # Simplified: assume points are snapped
            snapped_points = [
                {
                    **point,
                    'snapped': True,
                    'snapped_lat': point.get('lat'),
                    'snapped_lon': point.get('lon'),
                    'confidence': 0.95
                }
                for point in points
            ]

            # Publish snapped points
            for point in snapped_points:
                self.default_producer.send(
                    'gps.snapped',
                    value=point
                )

            # Check for re-routing triggers
            await self._check_reroute_trigger(vehicle_id, snapped_points)

            # Clear buffer
            self.vehicle_buffers[vehicle_id] = []

            logger.debug(f"Processed {len(points)} GPS points for {vehicle_id}")

        except Exception as e:
            logger.error(f"Error in GPS batch processing: {e}")

    async def _check_reroute_trigger(self, vehicle_id: str, snapped_points: list):
        """
        Determine if vehicle should be re-routed based on:
        - Traffic conditions
        - SLA breach risk
        - Accidents/obstacles ahead
        """
        if not snapped_points:
            return

        latest_point = snapped_points[-1]

        # In production:
        # 1. Query current traffic ahead
        # 2. Query vehicle's active route and SLA
        # 3. Check for accidents/obstacles
        # 4. Compare estimated arrival vs. SLA deadline
        # 5. If issues detected, publish reroute trigger

        # Example trigger
        trigger_reroute = False

        if trigger_reroute:
            self.default_producer.send(
                'reroute.triggered',
                value={
                    'vehicle_id': vehicle_id,
                    'lat': latest_point['lat'],
                    'lon': latest_point['lon'],
                    'reason': 'traffic_delay',
                    'timestamp': datetime.now().isoformat()
                }
            )

    async def process_traffic_stream(self):
        """
        Process real-time traffic events
        Aggregate into segments, detect patterns, alert affected vehicles
        """
        consumer = KafkaConsumer(
            'traffic.update',
            bootstrap_servers=self.bootstrap_servers,
            group_id='traffic-processor',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest'
        )

        logger.info("Traffic stream processor started")

        traffic_cache = {}  # segment_id -> traffic_event

        for message in consumer:
            try:
                event = message.value

                # Update cache
                segment_id = event.get('segment_id')
                traffic_cache[segment_id] = event

                # Identify affected vehicles (in production, spatial query)
                affected_vehicles = self._find_affected_vehicles(event)

                # Publish alert for each vehicle
                for v_id in affected_vehicles:
                    self.default_producer.send(
                        'alerts.hazard',  # Or traffic.alert (new topic)
                        value={
                            'vehicle_id': v_id,
                            'event_type': 'traffic',
                            'severity': event.get('severity'),
                            'delay_minutes': event.get('delay_minutes'),
                            'description': event.get('description'),
                            'timestamp': datetime.now().isoformat()
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing traffic event: {e}")

    def _find_affected_vehicles(self, traffic_event: Dict) -> list:
        """Find vehicles whose active routes intersect with traffic event"""
        # In production: spatial query against active routes
        return []

    async def process_analytics_stream(self):
        """
        Aggregate GPS data into analytics metrics
        - Daily distance/time/fuel
        - Driving behavior (harsh brakes, speeding)
        - SLA compliance
        """
        consumer = KafkaConsumer(
            'gps.snapped',
            bootstrap_servers=self.bootstrap_servers,
            group_id='analytics-aggregator',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest'
        )

        logger.info("Analytics aggregator started")

        # Aggregation window (e.g., 1 hour)
        metrics_buffer = defaultdict(lambda: {
            'distance_m': 0,
            'duration_s': 0,
            'harsh_brakes': 0,
            'speeding_events': 0,
            'points': 0
        })

        for message in consumer:
            try:
                point = message.value
                vehicle_id = point.get('vehicle_id')
                date_key = datetime.fromisoformat(point['timestamp']).date()
                key = f"{vehicle_id}:{date_key}"

                # Update metrics
                metrics = metrics_buffer[key]
                metrics['points'] += 1

                if point.get('harsh_braking'):
                    metrics['harsh_brakes'] += 1

                if point.get('speed_kmh', 0) > 120:  # Assuming 120 km/h limit
                    metrics['speeding_events'] += 1

                # Flush every 1000 points or periodically
                if metrics['points'] >= 1000:
                    self.default_producer.send(
                        'analytics.metrics',
                        value={
                            'vehicle_id': vehicle_id,
                            'date': str(date_key),
                            **metrics
                        }
                    )
                    metrics_buffer[key] = {
                        'distance_m': 0,
                        'duration_s': 0,
                        'harsh_brakes': 0,
                        'speeding_events': 0,
                        'points': 0
                    }

            except Exception as e:
                logger.error(f"Error in analytics aggregation: {e}")

    async def process_hazard_stream(self):
        """
        Process hazard detection events
        Correlate with routes, generate alerts
        """
        consumer = KafkaConsumer(
            'alerts.hazard',
            bootstrap_servers=self.bootstrap_servers,
            group_id='hazard-processor',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest'
        )

        logger.info("Hazard processor started")

        for message in consumer:
            try:
                hazard = message.value
                vehicle_id = hazard.get('vehicle_id')

                # In production: find route ahead, check if hazard is on path
                # Generate contextual alert

                logger.info(f"Hazard for {vehicle_id}: {hazard.get('type')}")

            except Exception as e:
                logger.error(f"Error processing hazard: {e}")

    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Kafka Stream Processor...")
        
        if self.default_producer:
            self.default_producer.flush()
            self.default_producer.close()

        for consumer in self.consumers.values():
            consumer.close()

        logger.info("✓ Shutdown complete")


# Django integration
def start_kafka_processor():
    """
    Start Kafka processor in Django app
    Call from management command or celery task
    """
    processor = KafkaStreamProcessor()
    processor.initialize()

    # Run async tasks
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(
            processor.process_gps_stream(),
            processor.process_traffic_stream(),
            processor.process_analytics_stream(),
            processor.process_hazard_stream()
        ))
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        processor.shutdown()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    start_kafka_processor()
