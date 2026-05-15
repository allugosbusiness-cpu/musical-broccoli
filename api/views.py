from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import *
from .serializers import *

class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for location data
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    
    def get_queryset(self):
        queryset = Location.objects.all()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
           
        # Filter by driver
        driver_id = self.request.query_params.get('driver_id', None)
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
           
        # Filter by truck
        truck_id = self.request.query_params.get('truck_id', None)
        if truck_id:
            queryset = queryset.filter(truck_id=truck_id)
           
        return queryset

class MissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for missions
    """
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer
    
    def get_queryset(self):
        queryset = Mission.objects.all()
        
        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
           
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__lte=end_date)
           
        # Filter by driver
        driver_id = self.request.query_params.get('driver_id', None)
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
           
        # Filter by truck
        truck_id = self.request.query_params.get('truck_id', None)
        if truck_id:
            queryset = queryset.filter(truck_id=truck_id)
           
        return queryset

class MissionTemplateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for mission templates
    """
    queryset = MissionTemplate.objects.all()
    serializer_class = MissionTemplateSerializer
    
    def get_queryset(self):
        queryset = MissionTemplate.objects.all()
        
        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
           
        # Filter by vehicle type
        vehicle_type = self.request.query_params.get('vehicle_type', None)
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)
           
        # Filter by driver requirements
        requires_driver = self.request.query_params.get('requires_driver', None)
        if requires_driver is not None:
            queryset = queryset.filter(requires_driver=requires_driver)
           
        return queryset

class DriverViewSet(viewsets.ModelViewSet):
    """
    API endpoint for drivers
    """
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    
    def get_queryset(self):
        queryset = Driver.objects.all()
        
        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
           
        # Filter by availability
        available = self.request.query_params.get('available', None)
        if available is not None:
            queryset = queryset.filter(is_available=available)
           
        # Filter by license type
        license_type = self.request.query_params.get('license_type', None)
        if license_type:
            queryset = queryset.filter(license_type=license_type)
           
        return queryset

class TruckViewSet(viewsets.ModelViewSet):
    """
    API endpoint for trucks
    """
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer
    
    def get_queryset(self):
        queryset = Truck.objects.all()
        
        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
           
        # Filter by availability
        available = self.request.query_params.get('available', None)
        if available is not None:
            queryset = queryset.filter(is_available=available)
           
        # Filter by truck type
        truck_type = self.request.query_params.get('truck_type', None)
        if truck_type:
            queryset = queryset.filter(truck_type=truck_type)
           
        # Filter by current location
        lat = self.request.query_params.get('lat', None)
        lng = self.request.query_params.get('lng', None)
        radius = self.request.query_params.get('radius', None)
        if lat and lng and radius:
            # This is a simplified version - in production you'd use PostGIS or similar
            pass
           
        return queryset

class DutyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for duties
    """
    queryset = Duty.objects.all()
    serializer_class = DutySerializer
    
    def get_queryset(self):
        queryset = Duty.objects.all()
        
        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
           
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__lte=end_date)
           
        # Filter by driver
        driver_id = self.request.query_params.get('driver_id', None)
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
           
        return queryset

class TruckLocationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for truck location history
    """
    queryset = TruckLocation.objects.all()
    serializer_class = TruckLocationSerializer
    
    def get_queryset(self):
        queryset = TruckLocation.objects.all()
        
        # Filter by truck
        truck_id = self.request.query_params.get('truck_id', None)
        if truck_id:
            queryset = queryset.filter(truck_id=truck_id)
           
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
           
        # Filter by driver
        driver_id = self.request.query_params.get('driver_id', None)
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
           
        return queryset

class DashboardViewSet(viewsets.ViewSet):
    """
    API endpoint for dashboard data
    """
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get dashboard statistics"""
        stats = {
            'total_trucks': Truck.objects.count(),
            'active_trucks': Truck.objects.filter(is_active=True).count(),
            'total_drivers': Driver.objects.count(),
            'active_drivers': Driver.objects.filter(is_active=True).count(),
            'total_missions': Mission.objects.count(),
            'active_missions': Mission.objects.filter(status='active').count(),
            'completed_missions_today': Mission.objects.filter(
                status='completed',
                end_time__date=timezone.now().date()
            ).count(),
            'pending_alerts': Alert.objects.filter(is_resolved=False).count(),
        }
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent activity for dashboard"""
        recent_missions = Mission.objects.order_by('-start_time')[:5]
        recent_alerts = Alert.objects.filter(is_resolved=False).order_by('-created_at')[:5]
        recent_locations = TruckLocation.objects.order_by('-timestamp')[:10]
        
        return Response({
            'recent_missions': MissionSerializer(recent_missions, many=True).data,
            'recent_alerts': AlertSerializer(recent_alerts, many=True).data,
            'recent_locations': TruckLocationSerializer(recent_locations, many=True).data,
        })

class CurrentLocationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for current location of trucks and drivers
    """
    serializer_class = CurrentLocationSerializer
    
    def get_queryset(self):
        # Return active trucks with their current location
        return Truck.objects.filter(
            is_active=True,
            current_mission__isnull=False
        ).select_related('current_mission', 'assigned_driver')
    
    @action(detail=False, methods=['get'])
    def all(self, request):
        """Get current location of all active trucks"""
        trucks = self.get_queryset()
        serializer = self.get_serializer(trucks, many=True)
        return Response(serializer.data)
       
    @action(detail=False, methods=['get'])
    def by_mission(self, request):
        """Get current location of trucks in a specific mission"""
        mission_id = request.query_params.get('mission_id', None)
        if mission_id:
            trucks = Truck.objects.filter(
                is_active=True,
                current_mission_id=mission_id
            ).select_related('current_mission', 'assigned_driver')
            serializer = self.get_serializer(trucks, many=True)
            return Response(serializer.data)
        return Response([])
       
    @action(detail=False, methods=['get'])
    def by_driver(self, request):
        """Get current location of trucks assigned to a specific driver"""
        driver_id = request.query_params.get('driver_id', None)
        if driver_id:
            trucks = Truck.objects.filter(
                is_active=True,
                assigned_driver_id=driver_id
            ).select_related('current_mission', 'assigned_driver')
            serializer = self.get_serializer(trucks, many=True)
            return Response(serializer.data)
        return Response([])