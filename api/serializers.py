from rest_framework import serializers
from .models import (
    FleetDriver, FleetTruck, FleetMission, FleetMissionStop, 
    FleetMissionEvent, FleetMissionDispute, FleetDriverPerformanceDaily, 
    FleetAdminAuditLog, TruckLocation, FleetActivity
)

# ============================================================
# TRUCK SERIALIZER (Frontend Compatibility Layer)
# ============================================================
class TruckSerializer(serializers.ModelSerializer):
    # Frontend expects 'id', but we use 'truck_identifier' for the map/labels
    id = serializers.CharField(source='truck_identifier', read_only=True)
    # Frontend expects 'coordinates' as {lat: x, lng: y}
    coordinates = serializers.SerializerMethodField()
    # Frontend expects 'driver' as a string name
    driver = serializers.SerializerMethodField()
    
    class Meta:
        model = FleetTruck
        fields = [
            'id', 'plate', 'driver', 'status', 'coordinates', 
            'last_latitude', 'last_longitude', 'speed_kmh', 
            'truck_identifier', 'assigned_driver'
        ]

    def get_coordinates(self, obj):
        if obj.last_latitude and obj.last_longitude:
            return {'lat': float(obj.last_latitude), 'lng': float(obj.last_longitude)}
        return {'lat': 0, 'lng': 0}

    def get_driver(self, obj):
        return obj.assigned_driver.get_display_name() if obj.assigned_driver else "Unassigned"

class TruckListSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='truck_identifier', read_only=True)
    coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = FleetTruck
        fields = ['id', 'plate', 'status', 'coordinates', 'speed_kmh']

    def get_coordinates(self, obj):
        if obj.last_latitude and obj.last_longitude:
            return {'lat': float(obj.last_latitude), 'lng': float(obj.last_longitude)}
        return {'lat': 0, 'lng': 0}

# ============================================================
# MISSION SERIALIZERS
# ============================================================
class MissionSerializer(serializers.ModelSerializer):
    # Frontend expects 'id' to be the mission number often
    id = serializers.CharField(source='mission_number', read_only=True)
    driver_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FleetMission
        fields = [
            'id', 'mission_number', 'status', 'priority', 'origin', 
            'destination', 'current_location', 'progress_pct', 'driver_name'
        ]

    def get_driver_name(self, obj):
        return obj.driver.get_display_name() if obj.driver else "Unassigned"

# ============================================================
# DRIVER SERIALIZERS
# ============================================================
class DriverSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = FleetDriver
        fields = ['id', 'name', 'phone_number', 'status', 'performance_mark']

    def get_name(self, obj):
        return obj.get_display_name()

# ============================================================
# COMPATIBILITY LAYER FOR REMAINING MODELS
# ============================================================

class CheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = FleetMissionStop
        fields = ['id', 'mission', 'stop_order', 'address', 'status']

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = FleetActivity
        fields = '__all__'

# Alias for mobile_endpoints.py
AlertSerializer = ActivitySerializer

class DriverPerformanceDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = FleetDriverPerformanceDaily
        fields = '__all__'
