"""
Fleet Management v2.0 - Clean Data Models
Django ORM definitions for Drivers, Trucks, Missions
Database: SQLite (dev), PostgreSQL (prod)
"""

from django.db import models
from django.utils import timezone
import uuid


class FleetMissionManager(models.Manager):
    """Custom manager that safely creates missions without optional speed fields"""
    def create(self, **kwargs):
        # Remove optional fields that may not exist in production DB
        # These will be added by migration later
        kwargs.pop('max_speed', None)
        kwargs.pop('avg_speed', None)
        kwargs.pop('compressed_trail', None)
        return super().create(**kwargs)


class FleetDriver(models.Model):
    """Driver information and tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fleet_id = models.UUIDField(blank=True, null=True, db_index=True)
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True, db_index=True)
    email = models.EmailField(unique=True, blank=True, null=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('suspended', 'Suspended'), ('terminated', 'Terminated'), ('on_leave', 'On Leave')],
        default='active',
        db_index=True
    )
    on_duty = models.BooleanField(default=False, db_index=True)
    truck = models.ForeignKey('FleetTruck', on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    performance_mark = models.DecimalField(max_digits=8, decimal_places=2, default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fleet_drivers'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class FleetTruck(models.Model):
    """Truck fleet management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fleet_id = models.UUIDField(blank=True, null=True, db_index=True)
    truck_identifier = models.CharField(max_length=100, unique=True, db_index=True)
    plate = models.CharField(max_length=20, unique=True, db_index=True)
    vin = models.CharField(max_length=50, unique=True, blank=True, null=True)
    telematics_id = models.CharField(max_length=100, unique=True, blank=True, null=True, db_index=True)
    fuel_capacity_liters = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    fuel_consumed_liters = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    odometer_km = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=[('idle', 'Idle'), ('enroute', 'En Route'), ('maintenance', 'Maintenance'), ('decommissioned', 'Decommissioned')],
        default='idle',
        db_index=True
    )
    last_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    last_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    last_location_ts = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fleet_trucks'

    def __str__(self):
        return self.truck_identifier


class TruckLocation(models.Model):
    """GPS location history for trucks"""
    id = models.BigAutoField(primary_key=True)
    truck = models.ForeignKey(FleetTruck, on_delete=models.CASCADE, related_name='location_history')
    driver = models.ForeignKey(FleetDriver, on_delete=models.SET_NULL, null=True, blank=True, related_name='location_history')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    speed = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    accuracy = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    altitude = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fleet_truck_locations'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.truck} @ {self.timestamp}"


class FleetMission(models.Model):
    """Mission/delivery tracking"""
    objects = FleetMissionManager()
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fleet_id = models.UUIDField(blank=True, null=True, db_index=True)
    mission_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=[('planned', 'Planned'), ('assigned', 'Assigned'), ('enroute', 'En Route'), ('paused', 'Paused'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        default='planned',
        db_index=True
    )
    priority = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')],
        default='normal'
    )
    truck = models.ForeignKey(FleetTruck, on_delete=models.SET_NULL, null=True, blank=True, related_name='missions')
    driver = models.ForeignKey(FleetDriver, on_delete=models.SET_NULL, null=True, blank=True, related_name='missions')
    origin = models.JSONField(default=dict, blank=True)
    destination = models.JSONField(default=dict, blank=True)
    distance_total_m = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    progress_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    cargo = models.JSONField(default=dict, blank=True)
    mission_date = models.DateField(blank=True, null=True, db_index=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # New fields for speed and compressed trail
    # Changed to null=True without defaults to prevent Django from including them in INSERT
    # These columns may not exist in production database until migration is applied
    max_speed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, editable=False)
    avg_speed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, editable=False)
    compressed_trail = models.JSONField(null=True, blank=True, help_text="Compressed list of [lat, lng, ts] for auditing", editable=False)

    def save(self, *args, **kwargs):
        # These optional fields may not exist as columns in production database yet
        # They are set to None, so Django won't include them in INSERT statements
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'fleet_missions'

    def __str__(self):
        return self.mission_number

    # Note: Logic to update max_speed, avg_speed, and compressed_trail should be handled
    # in the view or signal when TruckLocation is created for this mission.


class FleetActivity(models.Model):
    """Activity audit log"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck = models.ForeignKey(FleetTruck, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    driver = models.ForeignKey(FleetDriver, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    mission = models.ForeignKey(FleetMission, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    activity_type = models.CharField(
        max_length=20,
        choices=[('start', 'Start'), ('stop', 'Stop'), ('pause', 'Pause'), ('resume', 'Resume'), ('complete', 'Complete'), ('other', 'Other')],
        default='other',
        db_index=True
    )
    activity_category = models.CharField(max_length=50, default='mission')
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(db_index=True, auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fleet_activities'

    def __str__(self):
        return f"{self.activity_type} - {self.timestamp}"


class FleetDriverPerformanceDaily(models.Model):
    """Daily driver performance metrics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(FleetDriver, on_delete=models.CASCADE, related_name='daily_performance')
    date = models.DateField(db_index=True)
    missions_completed = models.IntegerField(default=0)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hours_on_duty = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, blank=True, null=True)
    incidents = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fleet_driver_performance_daily'

    def __str__(self):
        return f"{self.driver} - {self.date}"


class FleetAdminAuditLog(models.Model):
    """Admin audit log"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=200)
    admin_id = models.UUIDField(blank=True, null=True)
    target_type = models.CharField(max_length=50, blank=True, null=True)
    target_id = models.UUIDField(blank=True, null=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(db_index=True, auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fleet_admin_audit_logs'

    def __str__(self):
        return f"{self.action} - {self.timestamp}"


class Alert(models.Model):
    """System alerts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(
        max_length=50,
        choices=[('speed', 'Speeding'), ('temperature', 'Temperature'), ('maintenance', 'Maintenance'), ('location', 'Location'), ('delivery', 'Delivery'), ('other', 'Other')],
        db_index=True
    )
    severity = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        db_index=True
    )
    message = models.TextField()
    is_resolved = models.BooleanField(default=False, db_index=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'alerts'

    def __str__(self):
        return f"{self.alert_type} - {self.severity}"
