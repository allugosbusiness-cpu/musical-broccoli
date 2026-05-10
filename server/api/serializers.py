from rest_framework import serializers
from .models import (
    Truck, Checkpoint, Cargo, Alert, KPI, Route, TrackPoint, Location, 
    CurrentLocation, RouteOptimization, TruckFuel, FuelConsumption, FuelRefuel, FuelAlert
)

class CheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checkpoint
        fields = ['id', 'name', 'detail', 'status', 'timestamp']

class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ['id', 'cargo_type', 'weight', 'origin', 'destination', 'description']

class AlertSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Alert
        fields = ['id', 'truck', 'driver_name', 'alert_type', 'message', 'timestamp', 'is_resolved']

class TruckSerializer(serializers.ModelSerializer):
    checkpoints = CheckpointSerializer(many=True, read_only=True)
    cargo_info = CargoSerializer(read_only=True)
    alerts = AlertSerializer(many=True, read_only=True)
    current_route_id = serializers.CharField(source='current_route.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Truck
        fields = [
            'id', 'plate', 'driver', 'status', 'location', 'speed',
            'eta', 'progress', 'cargo', 'weight', 'coordinates',
            'origin', 'destination', 'origin_coordinates', 'destination_coordinates',
            'route_color', 'route_geojson',
            'current_route_id', 'auto_routing_enabled',
            'total_distance', 'distance_travelled',
            'checkpoints', 'cargo_info', 'alerts', 'last_updated', 'created_at'
        ]

class TruckListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list view - includes route data for map rendering"""
    current_route_id = serializers.CharField(source='current_route.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Truck
        fields = [
            'id', 'plate', 'driver', 'status', 'location', 'speed',
            'eta', 'progress', 'cargo', 'weight', 'last_updated',
            'total_distance', 'distance_travelled', 'coordinates',
            'origin', 'destination', 'origin_coordinates', 'destination_coordinates',
            'route_color', 'route_geojson',
            'current_route_id', 'auto_routing_enabled'
        ]

class KPISerializer(serializers.ModelSerializer):
    class Meta:
        model = KPI
        fields = [
            'id', 'date', 'active_trucks', 'on_time_rate', 'avg_speed',
            'total_deliveries', 'critical_alerts', 'timestamp'
        ]

class RouteSerializer(serializers.ModelSerializer):
    truck_plate = serializers.CharField(source='truck.plate', read_only=True)
    driver_name = serializers.CharField(source='truck.driver', read_only=True)
    
    class Meta:
        model = Route
        fields = [
            'id', 'truck', 'truck_plate', 'driver_name',
            'origin', 'destination', 'origin_coordinates', 'destination_coordinates',
            'waypoints', 'distance_km', 'estimated_duration_hours', 'status',
            'suggested_speeds', 'optimization_score', 'traffic_prediction', 'weather_factors',
            'current_waypoint_index', 'distance_travelled_km', 'time_elapsed_hours',
            'created_at', 'updated_at', 'started_at', 'completed_at'
        ]


class TrackPointSerializer(serializers.ModelSerializer):
    """Serializer for GPS track points (historical truck positions)"""
    truck_plate = serializers.CharField(source='truck.plate', read_only=True)
    
    class Meta:
        model = TrackPoint
        fields = [
            'id', 'truck', 'truck_plate', 'route',
            'latitude', 'longitude',
            'speed', 'heading', 'altitude', 'accuracy',
            'timestamp', 'recorded_at'
        ]
        read_only_fields = ['timestamp']


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location entities (origin, destination, checkpoints)"""
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'latitude', 'longitude', 'address',
            'location_type', 'average_dwell_time_minutes',
            'congestion_factor', 'accessibility_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CurrentLocationSerializer(serializers.ModelSerializer):
    """Serializer for current truck location with ML predictions"""
    truck_id = serializers.CharField(source='truck.id', read_only=True)
    truck_plate = serializers.CharField(source='truck.plate', read_only=True)
    
    class Meta:
        model = CurrentLocation
        fields = [
            'id', 'truck', 'truck_id', 'truck_plate',
            'latitude', 'longitude', 'speed', 'heading', 'altitude', 'accuracy',
            'predicted_next_location', 'predicted_arrival_time',
            'predicted_fuel_consumption_liters', 'traffic_ahead',
            'distance_to_next_checkpoint_km', 'distance_to_destination_km',
            'time_to_destination_minutes',
            'timestamp', 'recorded_at'
        ]
        read_only_fields = ['timestamp']


class RouteOptimizationSerializer(serializers.ModelSerializer):
    """Serializer for ML-based route optimization results"""
    truck_id = serializers.CharField(source='truck.id', read_only=True)
    truck_plate = serializers.CharField(source='truck.plate', read_only=True)
    
    class Meta:
        model = RouteOptimization
        fields = [
            'id', 'truck', 'truck_id', 'truck_plate', 'route',
            'original_distance_km', 'optimized_distance_km', 'distance_saved_percent',
            'original_time_hours', 'optimized_time_hours', 'time_saved_percent',
            'estimated_fuel_liters', 'fuel_cost_estimated', 'co2_emissions_kg',
            'alternative_routes', 'model_version', 'confidence_score', 'reasoning',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TruckFuelSerializer(serializers.ModelSerializer):
    """Serializer for truck fuel information"""
    truck_id = serializers.CharField(source='truck.id', read_only=True)
    truck_plate = serializers.CharField(source='truck.plate', read_only=True)
    fuel_percentage = serializers.SerializerMethodField()
    estimated_range_km = serializers.SerializerMethodField()
    
    class Meta:
        model = TruckFuel
        fields = [
            'id', 'truck', 'truck_id', 'truck_plate', 'vehicle_type',
            'tank_capacity_liters', 'current_fuel_liters', 'fuel_efficiency_kmpl',
            'fuel_percentage', 'estimated_range_km',
            'warning_level_percent', 'critical_level_percent',
            'total_fuel_consumed_liters', 'total_distance_traveled_km',
            'last_refuel_date', 'last_refuel_amount',
            'needs_refuel', 'is_low_fuel', 'is_critical_fuel',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_fuel_percentage(self, obj):
        """Calculate fuel percentage"""
        return round(obj.fuel_percentage(), 2)
    
    def get_estimated_range_km(self, obj):
        """Calculate estimated range"""
        return round(obj.estimated_range_km(), 2)


class FuelConsumptionSerializer(serializers.ModelSerializer):
    """Serializer for fuel consumption tracking"""
    truck_id = serializers.CharField(source='truck.id', read_only=True)
    truck_plate = serializers.CharField(source='truck.plate', read_only=True)
    route_id = serializers.CharField(source='route.id', read_only=True, allow_null=True)
    
    class Meta:
        model = FuelConsumption
        fields = [
            'id', 'truck', 'truck_id', 'truck_plate', 'route', 'route_id',
            'consumption_type', 'consumption_liters', 'distance_km', 'duration_minutes',
            'avg_speed_kmh', 'elevation_gain_m', 'elevation_loss_m', 'load_percent',
            'weather_conditions', 'efficiency_kmpl', 'efficiency_mpg',
            'fuel_before_liters', 'fuel_after_liters', 'consumption_factors',
            'start_timestamp', 'end_timestamp', 'was_predicted',
            'actual_vs_predicted_percent', 'created_at'
        ]
        read_only_fields = ['created_at']


class FuelRefuelSerializer(serializers.ModelSerializer):
    """Serializer for refueling events"""
    truck_id = serializers.CharField(source='truck.id', read_only=True)
    truck_plate = serializers.CharField(source='truck.plate', read_only=True)
    
    class Meta:
        model = FuelRefuel
        fields = [
            'id', 'truck', 'truck_id', 'truck_plate', 'amount_liters', 'cost_usd',
            'location', 'latitude', 'longitude',
            'fuel_before_liters', 'fuel_after_liters', 'fuel_price_per_liter',
            'refuel_timestamp', 'duration_minutes', 'driver_name', 'driver_notes',
            'fuel_efficiency_kmpl_before', 'distance_since_last_refuel_km',
            'created_at'
        ]
        read_only_fields = ['created_at']


class FuelAlertSerializer(serializers.ModelSerializer):
    """Serializer for fuel-related alerts"""
    truck_id = serializers.CharField(source='truck.id', read_only=True)
    truck_plate = serializers.CharField(source='truck.plate', read_only=True)
    
    class Meta:
        model = FuelAlert
        fields = [
            'id', 'truck', 'truck_id', 'truck_plate', 'alert_type', 'severity',
            'message', 'current_fuel_liters', 'current_fuel_percent',
            'estimated_range_km', 'is_acknowledged', 'is_resolved',
            'resolved_at', 'resolution_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
