"""
Fleet Management v2.0 - New Data Models (Fleet-prefixed to avoid conflicts)
Django ORM definitions for Drivers, Trucks, Missions

Database: SQLite (dev), PostgreSQL (prod)
Author: Backend Team
Date: 2026-05-05
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

# ============================================================
# CHOICES
# ============================================================

class DriverStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'
    TERMINATED = 'terminated', 'Terminated'
    ON_LEAVE = 'on_leave', 'On Leave'

class TruckStatus(models.TextChoices):
    IDLE = 'idle', 'Idle'
    ENROUTE = 'enroute', 'En Route'
    MAINTENANCE = 'maintenance', 'Maintenance'
    DECOMMISSIONED = 'decommissioned', 'Decommissioned'

class MissionStatus(models.TextChoices):
    PLANNED = 'planned', 'Planned'
    ASSIGNED = 'assigned', 'Assigned'
    ENROUTE = 'enroute', 'En Route'
    PAUSED = 'paused', 'Paused'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'

class MissionPriority(models.TextChoices):
    LOW = 'low', 'Low'
    NORMAL = 'normal', 'Normal'
    HIGH = 'high', 'High'
    URGENT = 'urgent', 'Urgent'

class MissionStopStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    SKIPPED = 'skipped', 'Skipped'

class MissionEventType(models.TextChoices):
    STATUS_CHANGED = 'status_changed', 'Status Changed'
    LOCATION_UPDATED = 'location_updated', 'Location Updated'
    STOP_COMPLETED = 'stop_completed', 'Stop Completed'
    DRIVER_ASSIGNED = 'driver_assigned', 'Driver Assigned'
    TRUCK_ASSIGNED = 'truck_assigned', 'Truck Assigned'
    PAUSED = 'paused', 'Mission Paused'
    RESUMED = 'resumed', 'Mission Resumed'
    DISPUTE_FILED = 'dispute_filed', 'Dispute Filed'

class ActivityType(models.TextChoices):
    """Comprehensive activity log types"""
    TRAIL_RECORDED = 'trail_recorded', 'Trail Recorded'
    MISSION_CREATED = 'mission_created', 'Mission Created'
    MISSION_STARTED = 'mission_started', 'Mission Started'
    MISSION_PAUSED = 'mission_paused', 'Mission Paused'
    MISSION_RESUMED = 'mission_resumed', 'Mission Resumed'
    MISSION_COMPLETED = 'mission_completed', 'Mission Completed'
    MISSION_CANCELLED = 'mission_cancelled', 'Mission Cancelled'
    LOCATION_UPDATE = 'location_update', 'Location Update'
    SPEED_RECORDED = 'speed_recorded', 'Speed Recorded'
    FUEL_UPDATE = 'fuel_update', 'Fuel Update'
    ALERT_TRIGGERED = 'alert_triggered', 'Alert Triggered'
    BREACH_DETECTED = 'breach_detected', 'Breach Detected'
    DRIVER_CHECK_IN = 'driver_check_in', 'Driver Check In'
    DRIVER_CHECK_OUT = 'driver_check_out', 'Driver Check Out'
    MAINTENANCE_ALERT = 'maintenance_alert', 'Maintenance Alert'
    SPEED_VIOLATION = 'speed_violation', 'Speed Violation'
    GEOFENCE_BREACH = 'geofence_breach', 'Geofence Breach'
    STOP_COMPLETED = 'stop_completed', 'Stop Completed'
    CARGO_UPDATE = 'cargo_update', 'Cargo Update'
    DISTANCE_RECORDED = 'distance_recorded', 'Distance Recorded'
    OTHER = 'other', 'Other'

class DisputeType(models.TextChoices):
    INCORRECT_LOCATION = 'incorrect_location', 'Incorrect Location'
    WRONG_CARGO = 'wrong_cargo', 'Wrong Cargo'
    TIMEOUT = 'timeout', 'Timeout'
    CUSTOMER_ISSUE = 'customer_issue', 'Customer Issue'
    SAFETY_CONCERN = 'safety_concern', 'Safety Concern'
    OTHER = 'other', 'Other'

class DisputeStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    RESOLVED = 'resolved', 'Resolved'
    DISMISSED = 'dismissed', 'Dismissed'

# ============================================================
# 1. FLEET DRIVER MODEL
# ============================================================

class FleetDriver(models.Model):
    """Driver profile with performance tracking."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fleet_id = models.UUIDField(db_index=True)
    
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True, db_index=True)  # For mobile app registration
    email = models.EmailField(unique=True, blank=True, null=True, db_index=True)
    
    license_number = models.CharField(max_length=50, unique=True, blank=True, null=True, db_index=True)
    license_state = models.CharField(max_length=10, blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)
    
    status = models.CharField(
        max_length=20, choices=DriverStatus.choices, default=DriverStatus.ACTIVE, db_index=True
    )
    on_duty = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)  # For mobile app login
    
    truck = models.ForeignKey(
        'FleetTruck', on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers'
    )  # Current assigned truck
    
    # Real-time location tracking from mobile app
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    current_speed = models.DecimalField(max_digits=6, decimal_places=2, default=0, blank=True, null=True)  # km/h
    last_location_update = models.DateTimeField(blank=True, null=True)
    
    performance_mark = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], db_index=True
    )
    deliveries_count = models.IntegerField(default=0)
    last_active_at = models.DateTimeField(blank=True, null=True)
    
    achievements = models.JSONField(blank=True, default=dict)
    photo_url = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_display_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def name(self):
        return self.get_display_name()
    
    def is_on_duty(self):
        return self.on_duty
    
    class Meta:
        db_table = 'fleet_drivers'
        indexes = [
            models.Index(fields=['fleet_id', 'status'], name='fleet_drv_fleet_st_idx'),
            models.Index(fields=['on_duty', 'status'], name='fleet_drv_on_duty_st_idx'),
            models.Index(fields=['-performance_mark'], name='fleet_drv_perf_idx'),
        ]
    
    def __str__(self):
        return self.get_display_name()

# ============================================================
# 2. FLEET TRUCK MODEL
# ============================================================

class FleetTruck(models.Model):
    """Truck vehicle with telemetry tracking."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fleet_id = models.UUIDField(db_index=True)
    
    truck_identifier = models.CharField(max_length=100, unique=True, db_index=True)
    plate = models.CharField(max_length=20, unique=True, db_index=True)
    vin = models.CharField(max_length=50, unique=True, blank=True, null=True)
    telematics_id = models.CharField(max_length=100, unique=True, blank=True, null=True, db_index=True)
    
    make = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    
    fuel_capacity_liters = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    fuel_consumed_liters = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    odometer_km = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    kilometers_travelled_km = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(
        max_length=20, choices=TruckStatus.choices, default=TruckStatus.IDLE, db_index=True
    )
    is_moving = models.BooleanField(default=False)
    
    last_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    last_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    last_location_ts = models.DateTimeField(blank=True, null=True)
    
    # Real-time tracking from mobile app
    current_location = models.JSONField(blank=True, null=True, default=dict)  # {'lat': float, 'lon': float, 'timestamp': iso}
    speed_kmh = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, default=0)
    
    assigned_driver = models.ForeignKey(FleetDriver, on_delete=models.SET_NULL, null=True, blank=True)
    maintenance_due_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        db_table = 'fleet_trucks'
        indexes = [
            models.Index(fields=['fleet_id', 'status'], name='fleet_trk_fleet_st_idx'),
            models.Index(fields=['plate'], name='fleet_truck_plate_idx'),
            models.Index(fields=['-updated_at'], name='fleet_truck_updated_idx'),
        ]
    
    def __str__(self):
        return f"{self.truck_identifier} ({self.plate})"

# ============================================================
# 3. FLEET MISSION MODEL
# ============================================================

class FleetMission(models.Model):
    """Mission/delivery with stops and tracking."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fleet_id = models.UUIDField(db_index=True)
    
    mission_number = models.CharField(max_length=100, unique=True, db_index=True)
    truck = models.ForeignKey(FleetTruck, on_delete=models.SET_NULL, null=True, blank=True)
    driver = models.ForeignKey(FleetDriver, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(
        max_length=20, choices=MissionStatus.choices, default=MissionStatus.PLANNED, db_index=True
    )
    priority = models.CharField(max_length=20, choices=MissionPriority.choices, default=MissionPriority.NORMAL)
    
    origin = models.JSONField()
    destination = models.JSONField()
    current_location = models.JSONField(blank=True, null=True)
    route_polyline = models.TextField(blank=True, null=True)
    
    distance_total_m = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    distance_remaining_m = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    progress_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    speed_kmh = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    eta = models.DateTimeField(blank=True, null=True)
    
    cargo = models.JSONField(blank=True, default=dict)
    stops = models.JSONField(blank=True, default=list)
    
    mission_date = models.DateField(blank=True, null=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True, db_index=True)  # When driver reached destination
    updated_at = models.DateTimeField(auto_now=True)
    created_by_admin_id = models.UUIDField(blank=True, null=True)
    
    def is_active(self):
        return self.status in [MissionStatus.ENROUTE, MissionStatus.PAUSED]
    
    def is_delivered(self):
        return self.delivered_at is not None or self.status == MissionStatus.COMPLETED
    
    class Meta:
        db_table = 'fleet_missions'
        indexes = [
            models.Index(fields=['fleet_id', 'status'], name='fleet_mis_fleet_st_idx'),
            models.Index(fields=['truck_id', 'status'], name='fleet_mis_truck_st_idx'),
            models.Index(fields=['driver_id', 'status'], name='fleet_mis_drv_st_idx'),
            models.Index(fields=['-created_at'], name='fleet_mis_cr_idx'),
        ]
    
    def __str__(self):
        return f"{self.mission_number} - {self.get_status_display()}"

# ============================================================
# 4. FLEET MISSION STOP MODEL
# ============================================================

class FleetMissionStop(models.Model):
    """Individual stop within a mission."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mission = models.ForeignKey(FleetMission, on_delete=models.CASCADE, related_name='stops_detail')
    
    stop_order = models.IntegerField()
    address = models.CharField(max_length=500)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    status = models.CharField(
        max_length=20, choices=MissionStopStatus.choices, default=MissionStopStatus.PENDING, db_index=True
    )
    arrived_at = models.DateTimeField(blank=True, null=True)
    departed_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fleet_mission_stops'
        unique_together = ('mission', 'stop_order')
        indexes = [
            models.Index(fields=['mission', 'stop_order'], name='fleet_stop_mission_order_idx'),
            models.Index(fields=['status'], name='fleet_stop_status_idx'),
        ]
    
    def __str__(self):
        return f"{self.mission.mission_number} - Stop {self.stop_order}"

# ============================================================
# 5. FLEET MISSION EVENT MODEL (Audit Trail)
# ============================================================

class FleetMissionEvent(models.Model):
    """Event log for mission activities (for audit trail)."""
    
    id = models.BigAutoField(primary_key=True)
    mission = models.ForeignKey(FleetMission, on_delete=models.CASCADE, null=True, blank=True)
    truck = models.ForeignKey(FleetTruck, on_delete=models.CASCADE, null=True, blank=True)
    driver = models.ForeignKey(FleetDriver, on_delete=models.CASCADE, null=True, blank=True)
    
    event_type = models.CharField(max_length=50, choices=MissionEventType.choices)
    payload = models.JSONField(blank=True, default=dict)
    trace_id = models.UUIDField(db_index=True, default=uuid.uuid4)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'fleet_mission_events'
        indexes = [
            models.Index(fields=['-created_at'], name='fleet_event_created_idx'),
            models.Index(fields=['event_type', '-created_at'], name='fleet_event_type_created_idx'),
        ]

# ============================================================
# 6. FLEET MISSION DISPUTE MODEL
# ============================================================

class FleetMissionDispute(models.Model):
    """Dispute filed by driver for a mission stop."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mission = models.ForeignKey(FleetMission, on_delete=models.CASCADE)
    driver = models.ForeignKey(FleetDriver, on_delete=models.CASCADE)
    stop = models.ForeignKey(FleetMissionStop, on_delete=models.SET_NULL, null=True, blank=True)
    
    dispute_type = models.CharField(max_length=50, choices=DisputeType.choices)
    description = models.TextField()
    photo_url = models.URLField(blank=True, null=True)
    
    status = models.CharField(
        max_length=20, choices=DisputeStatus.choices, default=DisputeStatus.OPEN, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by_admin_id = models.UUIDField(blank=True, null=True)
    
    class Meta:
        db_table = 'fleet_mission_disputes'
        indexes = [
            models.Index(fields=['mission', 'status'], name='fleet_disp_mis_st_idx'),
            models.Index(fields=['driver', 'status'], name='fleet_disp_drv_st_idx'),
        ]

# ============================================================
# 7. FLEET DRIVER PERFORMANCE DAILY MODEL
# ============================================================

class FleetDriverPerformanceDaily(models.Model):
    """Daily performance metrics for drivers."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(FleetDriver, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    
    deliveries_count = models.IntegerField(default=0)
    on_time_count = models.IntegerField(default=0)
    late_count = models.IntegerField(default=0)
    harsh_braking_count = models.IntegerField(default=0)
    idling_minutes = models.IntegerField(default=0)
    
    fuel_efficiency_liters_per_100km = models.DecimalField(max_digits=5, decimal_places=2)
    safety_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    efficiency_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    overall_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fleet_driver_performance_daily'
        unique_together = ('driver', 'date')
        indexes = [
            models.Index(fields=['driver', '-date'], name='fleet_daily_drv_dt_idx'),
        ]

# ============================================================
# 8. FLEET ADMIN AUDIT LOG MODEL
# ============================================================

class FleetAdminAuditLog(models.Model):
    """Audit log for admin changes."""
    
    id = models.BigAutoField(primary_key=True)
    admin_id = models.UUIDField(db_index=True)
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.UUIDField()
    
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'fleet_admin_audit_logs'
        indexes = [
            models.Index(fields=['-created_at'], name='fleet_audit_created_idx'),
            models.Index(fields=['resource_type', 'resource_id'], name='fleet_audit_resource_idx'),
        ]

# ============================================================
# 9. TRUCK LOCATION HISTORY MODEL
# ============================================================

class TruckLocation(models.Model):
    """Historical location data for trucks from mobile app tracking."""
    
    id = models.BigAutoField(primary_key=True)
    truck = models.ForeignKey(FleetTruck, on_delete=models.CASCADE, related_name='location_history', db_index=True)
    driver = models.ForeignKey(FleetDriver, on_delete=models.SET_NULL, null=True, blank=True, related_name='location_history')
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    speed = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # km/h
    accuracy = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # meters
    altitude = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # meters
    
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fleet_truck_locations'
        indexes = [
            models.Index(fields=['truck', 'timestamp'], name='fleet_loc_truck_ts_idx'),
            models.Index(fields=['driver', 'timestamp'], name='fleet_loc_drv_ts_idx'),
            models.Index(fields=['-timestamp'], name='fleet_loc_timestamp_idx'),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.truck} @ {self.timestamp} ({self.speed}km/h)"


# ============================================================
# 10. COMPREHENSIVE ACTIVITY/AUDIT LOG MODEL
# ============================================================

class FleetActivity(models.Model):
    """
    Comprehensive audit log for all system activities.
    Records all events: trails, missions, alerts, breaches, fuel, locations, speed.
    Allows manager/owner to review all activities after weeks/months.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fleet_id = models.UUIDField(db_index=True)
    
    # Primary relationships
    truck = models.ForeignKey(FleetTruck, on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='activities', db_index=True)
    driver = models.ForeignKey(FleetDriver, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='activities', db_index=True)
    mission = models.ForeignKey(FleetMission, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='activities', db_index=True)
    
    # Activity classification
    activity_type = models.CharField(max_length=50, choices=ActivityType.choices, 
                                    default=ActivityType.OTHER, db_index=True)
    activity_category = models.CharField(max_length=20, choices=[
        ('mission', 'Mission'),
        ('location', 'Location'),
        ('speed', 'Speed'),
        ('fuel', 'Fuel'),
        ('alert', 'Alert'),
        ('breach', 'Breach'),
        ('driver', 'Driver'),
        ('maintenance', 'Maintenance'),
        ('trail', 'Trail'),
        ('cargo', 'Cargo'),
    ], db_index=True)
    
    # Location data
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    location_lon = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    location_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Tracking metrics
    speed_kmh = models.DecimalField(max_digits=6, decimal_places=2, default=0, blank=True, null=True)
    distance_m = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True)
    fuel_liters = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    fuel_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # Alert & Breach data
    alert_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], blank=True, null=True)
    breach_type = models.CharField(max_length=100, blank=True, null=True)
    violation_details = models.TextField(blank=True, null=True)
    
    # Mission context
    mission_status_before = models.CharField(max_length=20, blank=True, null=True)
    mission_status_after = models.CharField(max_length=20, blank=True, null=True)
    
    # Flexible metadata storage
    metadata = models.JSONField(blank=True, default=dict)
    
    # Timestamps
    activity_date = models.DateField(db_index=True)  # For easy date filtering
    activity_time = models.TimeField()
    timestamp = models.DateTimeField(auto_now_add=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Status & visibility
    is_critical = models.BooleanField(default=False, db_index=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'fleet_activities'
        indexes = [
            models.Index(fields=['fleet_id', 'activity_type', '-timestamp'], name='fleet_act_type_ts_idx'),
            models.Index(fields=['truck', 'activity_date'], name='fleet_act_truck_date_idx'),
            models.Index(fields=['driver', 'activity_date'], name='fleet_act_drv_date_idx'),
            models.Index(fields=['mission', '-timestamp'], name='fleet_act_mission_ts_idx'),
            models.Index(fields=['activity_category', '-timestamp'], name='fleet_act_cat_ts_idx'),
            models.Index(fields=['is_critical', '-timestamp'], name='fleet_act_critical_idx'),
            models.Index(fields=['-timestamp'], name='fleet_act_timestamp_idx'),
        ]
        ordering = ['-timestamp']
        verbose_name = 'Fleet Activity'
        verbose_name_plural = 'Fleet Activities'
    
    def __str__(self):
        truck_name = self.truck.truck_identifier if self.truck else 'Unknown'
        return f"{truck_name}: {self.get_activity_type_display()} @ {self.timestamp}"
    
    @property
    def is_recent(self):
        """Check if activity is from today"""
        from django.utils import timezone
        return self.activity_date == timezone.now().date()
    
    @property
    def display_location(self):
        """Return formatted location display"""
        if self.location_name:
            return self.location_name
        if self.location_lat and self.location_lon:
            return f"{float(self.location_lat):.4f}, {float(self.location_lon):.4f}"
        return "Unknown"


