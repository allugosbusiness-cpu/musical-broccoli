from rest_framework import serializers
from .models import (
    FleetDriver, 
    FleetTruck, 
    FleetMission, 
    FleetMissionStop, 
    FleetMissionEvent, 
    FleetMissionDispute, 
    FleetDriverPerformanceDaily, 
    FleetAdminAuditLog, 
    TruckLocation,
    FleetActivity  # <--- This was the missing piece causing the crash
)

# ============================================================
# DRIVER SERIALIZERS
# ============================================================

class DriverSerializer(serializers.ModelSerializer):
    """Driver profile serializer with computed fields"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FleetDriver
        fields = [
            'id', 'fleet_id', 'first_name', 'last_name', 'display_name',
            'phone', 'email', 'license_number', 'license_state', 'hire_date',
            'status', 'on_duty', 'performance_mark', 'deliveries_count',
            'last_active_at', 'achievements', 'photo_url', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'performance_mark', 'deliveries_count']
    
    def get_display_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class DriverListSerializer(serializers.ModelSerializer):
    """Simplified driver serializer for list views"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FleetDriver
        fields = [
            'id', 'fleet_id', 'first_name', 'last_name', 'display_name',
            'phone', 'email', 'status', 'on_duty', 'performance_mark', 
            'deliveries_count', 'last_active_at'
        ]
    
    def get_display_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


# ============================================================
# TRUCK SERIALIZERS
# ============================================================

class TruckSerializer(serializers.ModelSerializer):
    """Truck serializer with assigned driver details"""
    assigned_driver_name = serializers.SerializerMethodField()
    fuel_consumed_pct = serializers.SerializerMethodField()
    
    class Meta:
        model = FleetTruck
        fields = [
            'id', 'fleet_id', 'truck_identifier', 'plate', 'vin', 'telematics_id',
            'make', 'model', 'year', 'fuel_capacity_liters', 'fuel_consumed_liters',
            'fuel_consumed_pct', 'odometer_km', 'kilometers_travelled_km', 'status',
            'is_moving', 'last_latitude', 'last_longitude', 'last_location_ts',
            'assigned_driver', 'assigned_driver_name', 'maintenance_due_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'fuel_consumed_pct', 'fuel_consumed_liters',
            'odometer_km', 'kilometers_travelled_km', 'is_moving', 'last_latitude',
            'last_longitude', 'last_location_ts', 'assigned_driver', 'assigned_driver_name'
        ]
    
    def get_assigned_driver_name(self, obj):
        if obj.assigned_driver:
            return obj.assigned_driver.get_display_name()
        return None
    
    def get_fuel_consumed_pct(self, obj):
        if obj.fuel_capacity_liters > 0:
            return round(float(obj.fuel_consumed_liters) / float(obj.fuel_capacity_liters) * 100, 2)
        return 0


class TruckListSerializer(serializers.ModelSerializer):
    """Simplified truck serializer for list views"""
    assigned_driver_name = serializers.SerializerMethodField()
    fuel_consumed_pct = serializers.SerializerMethodField()
    
    class Meta:
        model = FleetTruck
        fields = [
            'id', 'fleet_id', 'truck_identifier', 'plate', 'status', 'is_moving',
            'last_latitude', 'last_longitude', 'last_location_ts', 'speed_kmh',
            'fuel_consumed_pct', 'assigned_driver', 'assigned_driver_name',
            'kilometers_travelled_km'
        ]
    
    def get_assigned_driver_name(self, obj):
        if obj.assigned_driver:
            return obj.assigned_driver.get_display_name()
        return None
    
    def get_fuel_consumed_pct(self, obj):
        if obj.fuel_capacity_liters > 0:
            return round(float(obj.fuel_consumed_liters) / float(obj.fuel_capacity_liters) * 100, 2)
        return 0


# ============================================================
# MISSION SERIALIZERS
# ============================================================

class MissionStopSerializer(serializers.ModelSerializer):
    """Mission stop serializer"""
    class Meta:
        model = FleetMissionStop
        fields = [
            'id', 'mission', 'stop_order', 'address', 'latitude', 'longitude',
            'status', 'arrived_at', 'departed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MissionEventSerializer(serializers.ModelSerializer):
    """Mission event serializer"""
    class Meta:
        model = FleetMissionEvent
        fields = [
            'id', 'mission', 'truck', 'driver', 'event_type', 'payload', 'trace_id', 'created_at'
        ]
        read_only_fields = ['id', 'trace_id', 'created_at']


class MissionDisputeSerializer(serializers.ModelSerializer):
    """Mission dispute serializer"""
    class Meta:
        model = FleetMissionDispute
        fields = [
            'id', 'mission', 'driver', 'stop', 'dispute_type', 'description',
            'photo_url', 'status', 'created_at', 'resolved_at', 'resolved_by_admin_id'
        ]
        read_only_fields = ['id', 'created_at', 'resolved_at']


class MissionSerializer(serializers.ModelSerializer):
    """Mission serializer with nested stops, events, disputes"""
    stops = MissionStopSerializer(source='stops_detail', many=True, read_only=True)
    events = MissionEventSerializer(source='fleetmissionevent_set', many=True, read_only=True)
    disputes = MissionDisputeSerializer(source='fleetmissiondispute_set', many=True, read_only=True)
    truck_identifier = serializers.CharField(source='truck.truck_identifier', read_only=True)
    driver_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FleetMission
        fields = [
            'id', 'fleet_id', 'mission_number', 'truck', 'truck_identifier', 'driver', 'driver_name',
            'status', 'priority', 'origin', 'destination', 'current_location', 'route_polyline',
            'distance_total_m', 'distance_remaining_m', 'progress_pct', 'speed_kmh', 'eta',
            'cargo', 'stops', 'events', 'disputes', 'mission_date', 'created_at', 'started_at', 'completed_at',
            'updated_at', 'created_by_admin_id'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'progress_pct', 'distance_remaining_m',
            'stops', 'events', 'disputes'
        ]
    
    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.get_display_name()
        return None


class MissionListSerializer(serializers.ModelSerializer):
    """Simplified mission serializer for list views"""
    truck_identifier = serializers.CharField(source='truck.truck_identifier', read_only=True)
    driver_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FleetMission
        fields = [
            'id', 'fleet_id', 'mission_number', 'truck_identifier', 'driver_name',
            'status', 'priority', 'origin', 'destination', 'progress_pct',
            'eta', 'mission_date', 'created_at'
        ]
    
    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.get_display_name()
        return None


# ============================================================
# PERFORMANCE SERIALIZERS
# ============================================================

class DriverPerformanceDailySerializer(serializers.ModelSerializer):
    """Daily performance metrics serializer"""
    driver_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FleetDriverPerformanceDaily
        fields = [
            'id', 'driver', 'driver_name', 'date', 'deliveries_count', 'on_time_count', 'late_count',
            'harsh_braking_count', 'idling_minutes', 'fuel_efficiency_liters_per_100km',
            'safety_score', 'efficiency_score', 'overall_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.get_display_name()
        return None


# ============================================================
# AUDIT LOG SERIALIZERS
# ============================================================

class AdminAuditLogSerializer(serializers.ModelSerializer):
    """Admin audit log serializer"""
    class Meta:
        model = FleetAdminAuditLog
        fields = [
            'id', 'admin_id', 'action', 'resource_type', 'resource_id',
            'old_values', 'new_values', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ============================================================
# ACTIVITY SERIALIZER (Compatibility layer)
# ============================================================

class ActivitySerializer(serializers.ModelSerializer):
    """Comprehensive activity serializer for all events and alerts"""
    class Meta:
        model = FleetActivity
        fields = '__all__'

# This allows mobile_endpoints.py and other files to find 'AlertSerializer'
AlertSerializer = ActivitySerializer
