from rest_framework import serializers
from .models import (
    FleetDriver, FleetTruck, FleetMission, 
    FleetDriverPerformanceDaily, FleetAdminAuditLog, TruckLocation, 
    FleetActivity, Alert
)


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = FleetDriver
        fields = [
            'id', 'first_name', 'last_name', 'phone_number', 'email', 
            'status', 'on_duty', 'truck', 'latitude', 'longitude', 
            'performance_mark', 'created_at', 'updated_at'
        ]


class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = FleetTruck
        fields = [
            'id', 'truck_identifier', 'plate', 'vin', 'telematics_id',
            'fuel_capacity_liters', 'fuel_consumed_liters', 'odometer_km',
            'status', 'last_latitude', 'last_longitude', 'last_location_ts',
            'created_at', 'updated_at'
        ]


class TruckLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TruckLocation
        fields = [
            'id', 'truck', 'driver', 'latitude', 'longitude',
            'speed', 'accuracy', 'altitude', 'timestamp', 'created_at'
        ]


class MissionSerializer(serializers.ModelSerializer):
    truck = serializers.PrimaryKeyRelatedField(
        queryset=FleetTruck.objects.all(),
        required=False,
        allow_null=True
    )
    driver = serializers.PrimaryKeyRelatedField(
        queryset=FleetDriver.objects.all(),
        required=False,
        allow_null=True
    )
    truck_name = serializers.SerializerMethodField(read_only=True)
    driver_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = FleetMission
        fields = [
            'id', 'mission_number', 'status', 'priority', 'truck', 'driver',
            'truck_name', 'driver_name',
            'origin', 'destination', 'distance_total_m', 'progress_pct',
            'cargo', 'mission_date', 'started_at', 'completed_at',
            'delivered_at', 'created_at', 'updated_at'
        ]
    
    def get_truck_name(self, obj):
        return obj.truck.truck_identifier if obj.truck else None
    
    def get_driver_name(self, obj):
        return f"{obj.driver.first_name} {obj.driver.last_name}" if obj.driver else None


class FleetActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = FleetActivity
        fields = [
            'id', 'truck', 'driver', 'mission', 'activity_type',
            'activity_category', 'description', 'timestamp', 'created_at', 'updated_at'
        ]


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FleetDriverPerformanceDaily
        fields = [
            'id', 'driver', 'date', 'missions_completed', 'distance_km',
            'hours_on_duty', 'rating', 'incidents', 'created_at', 'updated_at'
        ]


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            'id', 'alert_type', 'severity', 'message', 'is_resolved',
            'resolved_at', 'created_at', 'updated_at'
        ]