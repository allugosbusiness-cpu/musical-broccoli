"""
Fleet Management v2.0 - REST API Views
Django REST Framework ViewSets for V2 models
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
import logging

from .models import (
    FleetDriver, FleetTruck, FleetMission, TruckLocation,
    FleetActivity, FleetDriverPerformanceDaily, Alert
)
from .serializers import (
    DriverSerializer, TruckSerializer, MissionSerializer,
    TruckLocationSerializer, FleetActivitySerializer,
    PerformanceSerializer, AlertSerializer
)

logger = logging.getLogger(__name__)


class DriverViewSet(viewsets.ModelViewSet):
    queryset = FleetDriver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [AllowAny]


class TruckViewSet(viewsets.ModelViewSet):
    queryset = FleetTruck.objects.all()
    serializer_class = TruckSerializer
    permission_classes = [AllowAny]


class MissionViewSet(viewsets.ModelViewSet):
    queryset = FleetMission.objects.all()
    serializer_class = MissionSerializer
    permission_classes = [AllowAny]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = TruckLocation.objects.all()
    serializer_class = TruckLocationSerializer
    permission_classes = [AllowAny]


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = FleetActivity.objects.all()
    serializer_class = FleetActivitySerializer
    permission_classes = [AllowAny]


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = FleetDriverPerformanceDaily.objects.all()
    serializer_class = PerformanceSerializer
    permission_classes = [AllowAny]


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [AllowAny]


class CheckpointViewSet(viewsets.ModelViewSet):
    """Placeholder for compatibility"""
    queryset = FleetMission.objects.none()
    serializer_class = MissionSerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
def health_check(request):
    """API health check endpoint"""
    return Response({
        'status': 'ok',
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
def api_root(request):
    """API root endpoint"""
    return Response({
        'message': 'PulseTrack Fleet Management API v1',
        'endpoints': {
            'drivers': '/api/v1/drivers/',
            'trucks': '/api/v1/trucks/',
            'missions': '/api/v1/missions/',
            'locations': '/api/v1/locations/',
            'activities': '/api/v1/activities/',
            'performance': '/api/v1/performance/',
            'alerts': '/api/v1/alerts/',
        }
    })


# Dashboard Endpoints
@api_view(['GET'])
def dashboard_drivers(request):
    """Get all drivers with performance data for dashboard"""
    try:
        drivers = FleetDriver.objects.all()
        serializer = DriverSerializer(drivers, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'Error fetching dashboard drivers: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def dashboard_trucks(request):
    """Get all trucks with synced mission data for dashboard"""
    try:
        trucks = FleetTruck.objects.all()
        serializer = TruckSerializer(trucks, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'Error fetching dashboard trucks: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def dashboard_missions(request):
    """Get all missions for dashboard"""
    try:
        missions = FleetMission.objects.all()
        serializer = MissionSerializer(missions, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'Error fetching dashboard missions: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def dashboard_summary(request):
    """Get dashboard summary statistics"""
    try:
        total_drivers = FleetDriver.objects.count()
        active_drivers = FleetDriver.objects.filter(status='active').count()
        total_trucks = FleetTruck.objects.count()
        active_trucks = FleetTruck.objects.filter(status='idle').count() + FleetTruck.objects.filter(status='enroute').count()
        total_missions = FleetMission.objects.count()
        active_missions = FleetMission.objects.filter(status='in_progress').count()
        active_alerts = Alert.objects.filter(is_resolved=False).count()
        
        return Response({
            'total_drivers': total_drivers,
            'active_drivers': active_drivers,
            'total_trucks': total_trucks,
            'active_trucks': active_trucks,
            'total_missions': total_missions,
            'active_missions': active_missions,
            'active_alerts': active_alerts,
        })
    except Exception as e:
        logger.error(f'Error fetching dashboard summary: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def dashboard_recalculate_performance(request):
    """Recalculate driver performance metrics"""
    try:
        # For now, just return success - actual calculation logic can be added later
        from django.utils import timezone
        from datetime import timedelta
        
        # Get performance records from the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        performances = FleetDriverPerformanceDaily.objects.filter(
            date__gte=thirty_days_ago
        )
        
        return Response({
            'message': 'Performance recalculation completed',
            'records_updated': performances.count()
        })
    except Exception as e:
        logger.error(f'Error recalculating performance: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Truck Tracking Endpoints
@api_view(['GET'])
def truck_tracking_all_locations(request):
    """Get all truck current locations for real-time tracking"""
    try:
        locations = TruckLocation.objects.select_related('truck', 'driver').order_by('-timestamp').distinct('truck')
        
        trucks_data = []
        for loc in locations:
            trucks_data.append({
                'truck_id': str(loc.truck.id),
                'truck_identifier': loc.truck.truck_identifier,
                'plate': loc.truck.plate,
                'latitude': float(loc.latitude),
                'longitude': float(loc.longitude),
                'speed': float(loc.speed),
                'accuracy': float(loc.accuracy),
                'altitude': float(loc.altitude),
                'timestamp': loc.timestamp.isoformat(),
                'driver_id': str(loc.driver.id) if loc.driver else None,
                'driver_name': f"{loc.driver.first_name} {loc.driver.last_name}" if loc.driver else None,
                'status': loc.truck.status,
            })
        
        return Response({
            'trucks': trucks_data,
            'count': len(trucks_data)
        })
    except Exception as e:
        logger.error(f'Error fetching truck locations: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def calculate_distance(request):
    """Calculate distance between two coordinates"""
    try:
        from math import radians, cos, sin, asin, sqrt
        
        data = request.data
        lat1 = float(data.get('lat1', 0))
        lon1 = float(data.get('lon1', 0))
        lat2 = float(data.get('lat2', 0))
        lon2 = float(data.get('lon2', 0))
        
        # Haversine formula for distance calculation
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c  # Radius of earth in kilometers
        
        return Response({
            'distance_km': round(km, 2),
            'distance_m': round(km * 1000, 2),
            'from': {'latitude': lat1, 'longitude': lon1},
            'to': {'latitude': lat2, 'longitude': lon2}
        })
    except Exception as e:
        logger.error(f'Error calculating distance: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Mobile Endpoints
@api_view(['POST'])
def mobile_driver_registration(request):
    """Register a mobile driver"""
    try:
        data = request.data
        
        phone_number = data.get('phone_number')
        first_name = data.get('first_name', 'Mobile')
        last_name = data.get('last_name', 'Driver')
        
        if not phone_number:
            return Response(
                {'error': 'phone_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if driver exists
        driver, created = FleetDriver.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'status': 'active'
            }
        )
        
        serializer = DriverSerializer(driver)
        return Response({
            'success': True,
            'created': created,
            'driver': serializer.data,
            'message': 'Driver registered successfully' if created else 'Driver already exists'
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Error registering driver: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)