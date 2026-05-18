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
    class Meta:
        model = FleetMission
        fields = [
            'id', 'mission_number', 'status', 'priority', 'truck', 'driver',
            'origin', 'destination', 'distance_total_m', 'progress_pct',
            'cargo', 'mission_date', 'started_at', 'completed_at',
            'delivered_at', 'created_at', 'updated_at'
        ]


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