from django.db import models
from django.utils import timezone
from enum import Enum
import uuid

class TruckStatus(models.TextChoices):
    MOVING = 'moving', 'Moving'
    DELAYED = 'delayed', 'Delayed'
    STOPPED = 'stopped', 'Stopped'
    DELIVERED = 'delivered', 'Delivered'
    MAINTENANCE = 'maintenance', 'Maintenance'

class AlertType(models.TextChoices):
    CRITICAL = 'critical', 'Critical'
    WARNING = 'warning', 'Warning'
    INFO = 'info', 'Info'
    SUCCESS = 'success', 'Success'

class Truck(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    plate = models.CharField(max_length=20, unique=True)
    driver = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=TruckStatus.choices,
        default=TruckStatus.MOVING
    )
    location = models.CharField(max_length=100)
    
    # Foreign keys to Location model for origin/destination
    origin_location = models.ForeignKey(
        'Location', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='trucks_starting_here'
    )
    destination_location = models.ForeignKey(
        'Location', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='trucks_going_here'
    )
    
    # Fallback text fields for origin/destination (for backward compatibility)
    origin = models.CharField(max_length=100, default='Harare')
    destination = models.CharField(max_length=100, default='Bulawayo')
    origin_coordinates = models.JSONField(default=dict, null=True, blank=True)  # {lat, lng}
    destination_coordinates = models.JSONField(default=dict, null=True, blank=True)  # {lat, lng}
    
    # Route visualization
    route_color = models.CharField(
        max_length=7,
        default='#3b82f6',
        help_text='Hex color for route visualization (deterministic per truck)'
    )
    route_geojson = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text='GeoJSON LineString geometry for persistent route display'
    )
    
    speed = models.IntegerField(default=0)
    eta = models.CharField(max_length=50)
    progress = models.IntegerField(default=0)
    cargo = models.CharField(max_length=100)
    weight = models.CharField(max_length=20)
    coordinates = models.JSONField(default=dict)  # lat, lng
    distance_travelled = models.FloatField(default=0.0)
    total_distance = models.FloatField(default=1000.0)
    current_route = models.ForeignKey('Route', on_delete=models.SET_NULL, null=True, blank=True, related_name='truck_active')
    auto_routing_enabled = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'trucks'
    
    def __str__(self):
        return f"{self.id} - {self.plate}"

class Checkpoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='checkpoints')
    name = models.CharField(max_length=100)
    detail = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=[('done', 'Done'), ('active', 'Active'), ('pending', 'Pending')],
        default='pending'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'checkpoints'
    
    def __str__(self):
        return f"{self.truck.id} - {self.name}"

class Cargo(models.Model):
    CARGO_TYPES = [
        ('electronics', 'Electronics'),
        ('fmcg', 'FMCG'),
        ('agri', 'Agriculture'),
        ('pharma', 'Pharmaceuticals'),
        ('fuel', 'Fuel Tanks'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.OneToOneField(Truck, on_delete=models.CASCADE, related_name='cargo_info')
    cargo_type = models.CharField(max_length=20, choices=CARGO_TYPES)
    weight = models.FloatField()
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cargo'
    
    def __str__(self):
        return f"{self.truck.id} - {self.cargo_type}"

class Alert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(
        max_length=20,
        choices=AlertType.choices,
        default=AlertType.INFO
    )
    message = models.TextField()
    driver_name = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'alerts'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.truck.id} - {self.alert_type}"

class KPI(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(auto_now_add=True)
    active_trucks = models.IntegerField(default=0)
    on_time_rate = models.FloatField(default=0)
    avg_speed = models.FloatField(default=0)
    total_deliveries = models.IntegerField(default=0)
    critical_alerts = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kpi_metrics'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"KPI - {self.date}"

class Route(models.Model):
    RouteStatus = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('optimized', 'Optimized'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='routes')
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    origin_coordinates = models.JSONField(default=dict)  # {lat, lng}
    destination_coordinates = models.JSONField(default=dict)  # {lat, lng}
    waypoints = models.JSONField(default=list)  # List of {lat, lng, name, order}
    distance_km = models.FloatField(default=0)  # Total distance
    estimated_duration_hours = models.FloatField(default=0)  # Total time
    status = models.CharField(max_length=20, choices=RouteStatus, default='planned')
    
    # Route geometry (GeoJSON from OSRM)
    geometry = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text='GeoJSON LineString geometry from OSRM routing service'
    )
    
    # ML-based suggestions
    suggested_speeds = models.JSONField(default=dict)  # {segment: speed_kmh}
    optimization_score = models.FloatField(default=0)  # 0-100 (fuel efficiency)
    traffic_prediction = models.JSONField(default=dict)  # {segment: congestion_level}
    weather_factors = models.JSONField(default=dict)  # Temperature, rain, wind
    
    # Progress tracking
    current_waypoint_index = models.IntegerField(default=0)
    distance_travelled_km = models.FloatField(default=0)
    time_elapsed_hours = models.FloatField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'routes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.truck.id}: {self.origin} → {self.destination}"


class Location(models.Model):
    """Represents a fixed location (origin, destination, checkpoint, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.TextField(blank=True)
    location_type = models.CharField(
        max_length=20,
        choices=[
            ('warehouse', 'Warehouse'),
            ('delivery', 'Delivery Point'),
            ('checkpoint', 'Checkpoint'),
            ('hub', 'Distribution Hub'),
            ('station', 'Service Station'),
            ('other', 'Other')
        ],
        default='other'
    )
    
    # ML metadata
    average_dwell_time_minutes = models.FloatField(default=0)  # Average time truck stays here
    congestion_factor = models.FloatField(default=1.0)  # 1.0 = no congestion, >1 = congested
    accessibility_score = models.FloatField(default=1.0)  # Ease of access (for routing)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'locations'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['location_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.location_type})"


class CurrentLocation(models.Model):
    """Real-time current location of a truck with ML predictive features"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.OneToOneField(Truck, on_delete=models.CASCADE, related_name='current_location')
    
    # Current position
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # Movement data
    speed = models.FloatField(default=0)  # km/h
    heading = models.FloatField(null=True, blank=True)  # 0-360 degrees
    altitude = models.FloatField(null=True, blank=True)  # meters
    accuracy = models.FloatField(null=True, blank=True)  # GPS accuracy
    
    # ML predictions
    predicted_next_location = models.JSONField(default=dict)  # {lat, lng, location_name}
    predicted_arrival_time = models.DateTimeField(null=True, blank=True)  # ETA to next location
    predicted_fuel_consumption_liters = models.FloatField(default=0)  # Fuel needed to destination
    traffic_ahead = models.JSONField(default=dict)  # {congestion_level, delay_minutes}
    
    # Route context
    distance_to_next_checkpoint_km = models.FloatField(default=0)
    distance_to_destination_km = models.FloatField(default=0)
    time_to_destination_minutes = models.FloatField(default=0)
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    recorded_at = models.DateTimeField()  # When the GPS fix was recorded
    
    class Meta:
        db_table = 'current_locations'
    
    def __str__(self):
        return f"{self.truck.id} @ ({self.latitude:.4f}, {self.longitude:.4f})"


class TrackPoint(models.Model):
    """GPS track points for historical truck movement"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='track_points')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='track_points')
    
    # GPS coordinates
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # Metadata
    speed = models.FloatField(default=0)  # km/h
    heading = models.FloatField(null=True, blank=True)  # 0-360 degrees
    altitude = models.FloatField(null=True, blank=True)  # meters above sea level
    accuracy = models.FloatField(null=True, blank=True)  # GPS accuracy in meters
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    recorded_at = models.DateTimeField()  # When the GPS fix was recorded
    
    class Meta:
        db_table = 'track_points'
        ordering = ['recorded_at']
        indexes = [
            models.Index(fields=['truck', 'recorded_at']),
            models.Index(fields=['route', 'recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.truck.id} @ {self.recorded_at}"


class RouteOptimization(models.Model):
    """ML-based route optimization results and suggestions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='optimizations')
    route = models.OneToOneField(Route, on_delete=models.CASCADE, related_name='optimization')
    
    # Optimization metrics
    original_distance_km = models.FloatField()
    optimized_distance_km = models.FloatField()
    distance_saved_percent = models.FloatField()  # Percentage saving
    
    original_time_hours = models.FloatField()
    optimized_time_hours = models.FloatField()
    time_saved_percent = models.FloatField()
    
    # Fuel efficiency
    estimated_fuel_liters = models.FloatField()
    fuel_cost_estimated = models.FloatField()
    co2_emissions_kg = models.FloatField(default=0)
    
    # Alternative routes
    alternative_routes = models.JSONField(default=list)  # List of alternative route options
    
    # ML model info
    model_version = models.CharField(max_length=50, default='v1.0')
    confidence_score = models.FloatField(default=0.8)  # 0-1, confidence in optimization
    reasoning = models.TextField(blank=True)  # Why this optimization is suggested
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'route_optimizations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.truck.id} - {self.distance_saved_percent:.1f}% distance saved"


class TruckFuel(models.Model):
    """Tracks fuel tank information for each truck"""
    VEHICLE_TYPES = [
        ('light_truck', 'Light Truck'),
        ('medium_truck', 'Medium Truck'),
        ('heavy_truck', 'Heavy Truck'),
        ('semi_truck', 'Semi Truck'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.OneToOneField(Truck, on_delete=models.CASCADE, related_name='fuel_info')
    
    # Vehicle specifications
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, default='medium_truck')
    tank_capacity_liters = models.FloatField(default=100)
    current_fuel_liters = models.FloatField(default=100)
    fuel_efficiency_kmpl = models.FloatField(default=0.1)  # km per liter (calculated)
    
    # Thresholds
    warning_level_percent = models.IntegerField(default=25)  # Alert when below this
    critical_level_percent = models.IntegerField(default=10)  # Emergency alert
    
    # Tracking
    total_fuel_consumed_liters = models.FloatField(default=0)
    total_distance_traveled_km = models.FloatField(default=0)
    last_refuel_date = models.DateTimeField(null=True, blank=True)
    last_refuel_amount = models.FloatField(null=True, blank=True)
    
    # Status
    needs_refuel = models.BooleanField(default=False)
    is_low_fuel = models.BooleanField(default=False)
    is_critical_fuel = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'truck_fuel'
    
    def __str__(self):
        return f"{self.truck.id} - {self.current_fuel_liters}L / {self.tank_capacity_liters}L"
    
    def fuel_percentage(self):
        """Get current fuel as percentage of tank capacity"""
        return (self.current_fuel_liters / self.tank_capacity_liters) * 100 if self.tank_capacity_liters > 0 else 0
    
    def estimated_range_km(self):
        """Estimate how far truck can travel with current fuel"""
        return self.current_fuel_liters * self.fuel_efficiency_kmpl


class FuelConsumption(models.Model):
    """Track fuel consumption over time with detailed metrics"""
    
    CONSUMPTION_TYPES = [
        ('segment', 'Route Segment'),
        ('trip', 'Complete Trip'),
        ('idle', 'Idle Time'),
        ('refuel', 'Refuel Event'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='fuel_consumption')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='fuel_consumption')
    
    # Consumption type
    consumption_type = models.CharField(max_length=20, choices=CONSUMPTION_TYPES, default='segment')
    
    # Consumption metrics
    consumption_liters = models.FloatField()  # Actual fuel consumed
    distance_km = models.FloatField(default=0)
    duration_minutes = models.IntegerField(default=0)
    avg_speed_kmh = models.FloatField(default=0)
    
    # Environmental factors
    elevation_gain_m = models.FloatField(default=0)
    elevation_loss_m = models.FloatField(default=0)
    load_percent = models.FloatField(default=50)  # Cargo load as percentage
    
    # Weather conditions
    weather_conditions = models.JSONField(default=dict)  # {'rain': bool, 'wind_speed': km/h, ...}
    
    # Efficiency metrics
    efficiency_kmpl = models.FloatField(default=0)  # km per liter
    efficiency_mpg = models.FloatField(default=0)  # miles per gallon (imperial)
    
    # Fuel state
    fuel_before_liters = models.FloatField()
    fuel_after_liters = models.FloatField()
    
    # Breakdown of consumption factors
    consumption_factors = models.JSONField(default=dict)  # {speed_factor, load_factor, terrain_factor, weather_factor}
    
    # Timing
    start_timestamp = models.DateTimeField()
    end_timestamp = models.DateTimeField()
    
    # AI prediction
    was_predicted = models.BooleanField(default=False)  # Was this from ML prediction
    actual_vs_predicted_percent = models.FloatField(null=True, blank=True)  # Accuracy of prediction
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fuel_consumption'
        ordering = ['-start_timestamp']
        indexes = [
            models.Index(fields=['truck', '-start_timestamp']),
            models.Index(fields=['route', 'start_timestamp']),
        ]
    
    def __str__(self):
        return f"{self.truck.id} - {self.consumption_liters}L consumed"


class FuelRefuel(models.Model):
    """Log refueling events"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='refuel_events')
    
    # Refuel details
    amount_liters = models.FloatField()
    cost_usd = models.FloatField(default=0)
    location = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Fuel state before/after
    fuel_before_liters = models.FloatField()
    fuel_after_liters = models.FloatField()
    fuel_price_per_liter = models.FloatField(null=True, blank=True)
    
    # Timing
    refuel_timestamp = models.DateTimeField()
    duration_minutes = models.IntegerField(default=5)
    
    # Driver info
    driver_name = models.CharField(max_length=100, blank=True)
    driver_notes = models.TextField(blank=True)
    
    # Analytics
    fuel_efficiency_kmpl_before = models.FloatField(null=True, blank=True)
    distance_since_last_refuel_km = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fuel_refuel'
        ordering = ['-refuel_timestamp']
        indexes = [
            models.Index(fields=['truck', '-refuel_timestamp']),
        ]
    
    def __str__(self):
        return f"{self.truck.id} - {self.amount_liters}L @ {self.location}"


class FuelAlert(models.Model):
    """Alerts for fuel-related issues"""
    
    ALERT_SEVERITIES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.ForeignKey(Truck, on_delete=models.CASCADE, related_name='fuel_alerts')
    
    # Alert details
    alert_type = models.CharField(max_length=50)  # 'low_fuel', 'excessive_consumption', 'refuel_overdue', etc.
    severity = models.CharField(max_length=20, choices=ALERT_SEVERITIES, default='warning')
    message = models.TextField()
    
    # Context
    current_fuel_liters = models.FloatField()
    current_fuel_percent = models.FloatField()
    estimated_range_km = models.FloatField()
    
    # Resolution
    is_acknowledged = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fuel_alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.truck.id} - {self.alert_type}"
