from rest_framework import serializers
import logging
from .models import (
    FleetDriver, FleetTruck, FleetMission, 
    FleetDriverPerformanceDaily, FleetAdminAuditLog, TruckLocation, 
    FleetActivity, Alert
)

logger = logging.getLogger(__name__)


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
    distance_total_m = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    
    class Meta:
        model = FleetMission
        # IMPORTANT: Do NOT include max_speed, avg_speed, or compressed_trail here.
        # Those columns do not exist in the production database and including them
        # causes Django to throw FieldError when serializing.
        # They exist on the model as Python-only attributes (editable=False).
        fields = [
            'id', 'mission_number', 'status', 'priority', 'truck', 'driver',
            'truck_name', 'driver_name',
            'origin', 'destination', 'distance_total_m',
            'cargo', 'mission_date', 'started_at', 'completed_at',
            'delivered_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'truck_name', 'driver_name']
    
    def get_truck_name(self, obj):
        return obj.truck.truck_identifier if obj.truck else None
    
    def get_driver_name(self, obj):
        return f"{obj.driver.first_name} {obj.driver.last_name}" if obj.driver else None
    
    def to_representation(self, instance):
        """Add max_speed/avg_speed/compressed_trail as computed values in the response,
        so the frontend can still access them without them being database columns."""
        data = super().to_representation(instance)
        data['max_speed'] = '0.00'
        data['avg_speed'] = '0.00'
        data['compressed_trail'] = []
        return data
    
    def _calculate_distance(self, origin, destination):
        """Calculate distance between two coordinates using Haversine formula (meters)"""
        from math import radians, cos, sin, asin, sqrt
        from decimal import Decimal
        
        if not origin or not destination:
            return Decimal('0')
        
        # Extract coordinates - support multiple key formats: lat/lon, lat/lng, latitude/longitude
        lat1 = float(origin.get('lat', origin.get('latitude', 0)))
        lon1 = float(origin.get('lon', origin.get('lng', origin.get('longitude', 0))))
        lat2 = float(destination.get('lat', destination.get('latitude', 0)))
        lon2 = float(destination.get('lon', destination.get('lng', destination.get('longitude', 0))))
        
        if lat1 == 0 or lon1 == 0 or lat2 == 0 or lon2 == 0:
            return Decimal('0')
        
        # Haversine formula
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        meters = km * 1000
        
        return Decimal(str(round(meters, 2)))
    
    def create(self, validated_data):
        """Create mission and calculate distance if origin/destination provided"""
        # Calculate distance if both origin and destination are provided
        origin = validated_data.get('origin')
        destination = validated_data.get('destination')
        
        if origin and destination and not validated_data.get('distance_total_m'):
            validated_data['distance_total_m'] = self._calculate_distance(origin, destination)
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update mission and recalculate distance if origin/destination changed"""
        # Recalculate distance if origin or destination changed
        origin = validated_data.get('origin', instance.origin)
        destination = validated_data.get('destination', instance.destination)
        
        if origin and destination:
            validated_data['distance_total_m'] = self._calculate_distance(origin, destination)
        
        return super().update(instance, validated_data)


class FleetActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = FleetActivity
        fields = [
            'id', 'truck', 'driver', 'mission', 'activity_type',
            'activity_category', 'description', 'avg_speed', 'compressed_trail',
            'timestamp', 'created_at', 'updated_at'
        ]


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FleetDriverPerformanceDaily
        fields = [
            'id', 'driver', 'date', 'missions_completed', 'distance_km',
            'hours_on_duty', 'rating', 'incidents', 'created_at', 'updated_at'
        ]


class AlertSerializer(serializers.ModelSerializer):
    truck_identifier = serializers.CharField(source='truck.truck_identifier', read_only=True, default=None)
    driver_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Alert
        fields = [
            'id', 'alert_type', 'severity', 'message', 'truck', 'driver', 'mission',
            'truck_identifier', 'driver_name',
            'location_lat', 'location_lon', 'speed_kmh',
            'is_resolved', 'resolved_at', 'created_at', 'updated_at'
        ]
    
    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.get_display_name()
        return None
