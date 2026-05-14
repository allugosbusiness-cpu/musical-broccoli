"""
Fleet Management v2.0 - REST API Views & Serializers
Django REST Framework ViewSets and Serializers for all v2 models
Implements RBAC, pagination, filtering, and nested relationships

Author: Backend Team
Date: 2026-05-05
"""

from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.conf import settings
import logging
import requests
import traceback

from .models_v2 import (
    FleetDriver, FleetTruck, FleetMission, FleetMissionStop, FleetMissionEvent, 
    FleetMissionDispute, FleetDriverPerformanceDaily, FleetAdminAuditLog
)
from .services_v2 import (
    DriverService, TruckService, MissionService, DisputeService, ComputedFieldsWorker
)

logger = logging.getLogger(__name__)

# ============================================================
# SERIALIZERS
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
        extra_kwargs = {
            'fleet_id': {'required': True},
            'truck_identifier': {'required': True},
            'plate': {'required': True},
            'vin': {'required': False, 'allow_null': True},
            'telematics_id': {'required': False, 'allow_null': True},
            'make': {'required': False, 'allow_null': True},
            'model': {'required': False, 'allow_null': True},
            'year': {'required': False, 'allow_null': True},
            'fuel_capacity_liters': {'required': False, 'default': 100},
            'status': {'required': False, 'default': 'IDLE'},
            'maintenance_due_date': {'required': False, 'allow_null': True},
        }
    
    def get_assigned_driver_name(self, obj):
        if obj.assigned_driver:
            return obj.assigned_driver.get_display_name()
        return None
    
    def get_fuel_consumed_pct(self, obj):
        if obj.fuel_capacity_liters > 0:
            return round(float(obj.fuel_consumed_liters) / float(obj.fuel_capacity_liters) * 100, 2)
        return 0


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
    """Mission event serializer (read-only, for audit trail)"""
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


class DriverPerformanceDailySerializer(serializers.ModelSerializer):
    """Daily performance metrics serializer"""
    class Meta:
        model = FleetDriverPerformanceDaily
        fields = [
            'id', 'driver', 'date', 'deliveries_count', 'on_time_count', 'late_count',
            'harsh_braking_count', 'idling_minutes', 'fuel_efficiency_liters_per_100km',
            'safety_score', 'efficiency_score', 'overall_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================
# VIEWSETS
# ============================================================

class DriverViewSet(viewsets.ModelViewSet):
    """
    API endpoint for driver management
    
    Endpoints:
    - GET /api/v1/drivers - List all drivers
    - POST /api/v1/drivers - Create driver (admin only)
    - GET /api/v1/drivers/{id} - Get driver details
    - PATCH /api/v1/drivers/{id} - Update driver (admin or self)
    - POST /api/v1/drivers/{id}/on-duty-toggle - Toggle on-duty status
    """
    queryset = FleetDriver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['fleet_id', 'status', 'on_duty']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['created_at', 'performance_mark', 'deliveries_count']
    
    def create(self, request, *args, **kwargs):
        """Create new driver (admin only)"""
        try:
            admin_id = request.user.id if hasattr(request.user, 'id') else None
            driver = DriverService.create_driver(
                fleet_id=request.data.get('fleet_id'),
                first_name=request.data.get('first_name'),
                last_name=request.data.get('last_name'),
                email=request.data.get('email'),
                phone=request.data.get('phone'),
                license_number=request.data.get('license_number'),
                hire_date=request.data.get('hire_date'),
                admin_id=admin_id
            )
            serializer = self.get_serializer(driver)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Failed to create driver: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def on_duty_toggle(self, request, pk=None):
        """Toggle driver on-duty status"""
        try:
            driver = self.get_object()
            on_duty = request.data.get('on_duty', not driver.on_duty)
            admin_id = request.user.id if hasattr(request.user, 'id') else None
            
            DriverService.toggle_on_duty(driver.id, on_duty, admin_id)
            driver.refresh_from_db()
            
            serializer = self.get_serializer(driver)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to toggle on-duty: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TruckViewSet(viewsets.ModelViewSet):
    """
    API endpoint for truck management
    
    Endpoints:
    - GET /api/v1/trucks - List all trucks
    - POST /api/v1/trucks - Create truck (admin only)
    - GET /api/v1/trucks/{id} - Get truck details
    - PATCH /api/v1/trucks/{id} - Update truck
    - PATCH /api/v1/trucks/{id}/assign - Assign driver to truck (admin only)
    """
    queryset = FleetTruck.objects.all().order_by('-created_at')
    serializer_class = TruckSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['fleet_id', 'status', 'plate']
    search_fields = ['truck_identifier', 'plate', 'telematics_id']
    ordering_fields = ['created_at', 'fuel_consumed_liters', 'odometer_km']
    ordering = ['-created_at']
    
    def create(self, request, *args, **kwargs):
        """Create new truck (admin only)"""
        try:
            # ✅ DEBUG: Log all request data
            logger.debug(f"📝 Create truck request data: {request.data}")
            
            admin_id = request.user.id if hasattr(request.user, 'id') else None
            
            # ✅ VALIDATE: Check required fields before calling service
            required_fields = ['fleet_id', 'truck_identifier', 'plate']
            missing_fields = [f for f in required_fields if not request.data.get(f)]
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                logger.error(f"❌ {error_msg}")
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            
            truck = TruckService.create_truck(
                fleet_id=request.data.get('fleet_id'),
                truck_identifier=request.data.get('truck_identifier'),
                plate=request.data.get('plate'),
                vin=request.data.get('vin'),
                telematics_id=request.data.get('telematics_id'),
                make=request.data.get('make'),
                model=request.data.get('model'),
                year=request.data.get('year'),
                fuel_capacity_liters=request.data.get('fuel_capacity_liters', 100),
                admin_id=admin_id
            )
            logger.info(f"✅ Truck created successfully: {truck.id} ({truck.plate})")
            serializer = self.get_serializer(truck)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"❌ Failed to create truck: {e}")
            logger.error(f"   Traceback: {traceback.format_exc()}")
            error_detail = {
                'error': str(e),
                'type': type(e).__name__,
                'details': traceback.format_exc() if settings.DEBUG else None
            }
            return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def assign(self, request, pk=None):
        """Assign driver to truck (admin only)"""
        try:
            truck = self.get_object()
            driver_id = request.data.get('driver_id')
            admin_id = request.user.id if hasattr(request.user, 'id') else None
            
            TruckService.assign_driver(truck.id, driver_id, admin_id)
            truck.refresh_from_db()
            
            serializer = self.get_serializer(truck)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to assign driver: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for mission management
    
    Endpoints:
    - GET /api/v1/missions - List missions
    - POST /api/v1/missions - Create mission (admin only)
    - GET /api/v1/missions/{id} - Get mission details with stops/events
    - PATCH /api/v1/missions/{id} - Update mission
    - PATCH /api/v1/missions/{id}/status - Change mission status
    - PATCH /api/v1/missions/{id}/stops/{stop_id} - Complete mission stop
    """
    queryset = FleetMission.objects.prefetch_related('stops_detail', 'fleetmissionevent_set', 'fleetmissiondispute_set')
    serializer_class = MissionSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['fleet_id', 'status', 'truck_id', 'driver_id']
    search_fields = ['mission_number', 'truck__plate', 'driver__email']
    ordering_fields = ['created_at', 'progress_pct', 'priority']
    
    def create(self, request, *args, **kwargs):
        """Create new mission (admin only)"""
        try:
            admin_id = request.user.id if hasattr(request.user, 'id') else None
            stops = request.data.get('stops', [])
            
            mission = MissionService.create_mission(
                fleet_id=request.data.get('fleet_id'),
                mission_number=request.data.get('mission_number'),
                truck_id=request.data.get('truck_id'),
                driver_id=request.data.get('driver_id'),
                origin=request.data.get('origin'),
                destination=request.data.get('destination'),
                current_location=request.data.get('current_location'),
                stops=stops,
                priority=request.data.get('priority', 'normal'),
                cargo=request.data.get('cargo', {}),
                route_polyline=request.data.get('route_polyline'),
                distance_total_m=request.data.get('distance_total_m', 0),
                status=request.data.get('status'),
                progress_pct=request.data.get('progress_pct', 0),
                admin_id=admin_id
            )
            serializer = self.get_serializer(mission)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Failed to create mission: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        """Change mission status with state machine validation"""
        try:
            mission = self.get_object()
            new_status = request.data.get('status')
            admin_id = request.user.id if hasattr(request.user, 'id') else None
            
            if new_status == 'assigned':
                MissionService.assign_mission(mission.id, admin_id=admin_id)
            elif new_status == 'enroute':
                MissionService.start_mission(mission.id, admin_id=admin_id)
            elif new_status == 'completed':
                MissionService.complete_mission(mission.id, admin_id=admin_id)
            
            mission.refresh_from_db()
            serializer = self.get_serializer(mission)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to update mission status: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], url_path='stops/(?P<stop_id>[^/.]+)')
    def complete_stop(self, request, pk=None, stop_id=None):
        """Mark a mission stop as completed"""
        try:
            mission = self.get_object()
            stop = get_object_or_404(FleetMissionStop, id=stop_id, mission=mission)
            
            MissionService.complete_stop(mission.id, stop.stop_order)
            mission.refresh_from_db()
            
            serializer = self.get_serializer(mission)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to complete stop: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MissionDisputeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for mission disputes
    
    Endpoints:
    - GET /api/v1/disputes - List disputes
    - POST /api/v1/disputes - File new dispute (driver only)
    - GET /api/v1/disputes/{id} - Get dispute details
    - PATCH /api/v1/disputes/{id}/resolve - Resolve dispute (admin only)
    """
    queryset = FleetMissionDispute.objects.all()
    serializer_class = MissionDisputeSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['mission', 'driver', 'status']
    search_fields = ['mission__mission_number', 'driver__email']
    ordering_fields = ['created_at', 'status']
    
    def create(self, request, *args, **kwargs):
        """File new dispute (driver only)"""
        try:
            driver_id = request.data.get('driver_id')
            mission_id = request.data.get('mission_id')
            
            dispute = DisputeService.file_dispute(
                mission_id=mission_id,
                driver_id=driver_id,
                dispute_type=request.data.get('dispute_type'),
                description=request.data.get('description'),
                photo_url=request.data.get('photo_url'),
                stop_id=request.data.get('stop_id')
            )
            serializer = self.get_serializer(dispute)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Failed to file dispute: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def resolve(self, request, pk=None):
        """Resolve dispute (admin only)"""
        try:
            dispute = self.get_object()
            admin_id = request.user.id if hasattr(request.user, 'id') else None
            
            DisputeService.resolve_dispute(
                dispute.id,
                resolution=request.data.get('resolution'),
                admin_id=admin_id
            )
            dispute.refresh_from_db()
            
            serializer = self.get_serializer(dispute)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to resolve dispute: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DriverPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for driver performance metrics (read-only)
    
    Endpoints:
    - GET /api/v1/performance - List daily performance records
    - GET /api/v1/performance/{id} - Get specific performance record
    """
    queryset = FleetDriverPerformanceDaily.objects.all()
    serializer_class = DriverPerformanceDailySerializer
    permission_classes = [AllowAny]
    filterset_fields = ['driver', 'date']
    ordering_fields = ['date', 'overall_score']
