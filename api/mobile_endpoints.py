# server/api/mobile_endpoints.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
import json
import qrcode
import uuid
from io import BytesIO
import base64
from datetime import datetime

from .models import FleetDriver, FleetTruck, FleetMission, TruckLocation, FleetActivity
from .serializers import TruckSerializer, AlertSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_health_check(request):
    diagnostics = {'status': 'unknown', 'timestamp': timezone.now().isoformat(), 'database': {}, 'message': ''}
    try:
        for model_name, model_cls in [('drivers', FleetDriver), ('trucks', FleetTruck), ('missions', FleetMission)]:
            try:
                diagnostics['database'][model_name] = {'status': 'ok', 'count': model_cls.objects.count()}
            except Exception as e:
                diagnostics['database'][model_name] = {'status': 'error', 'error': str(e)}
        
        db_errors = [v for v in diagnostics['database'].values() if v.get('status') == 'error']
        if db_errors:
            diagnostics['status'] = 'unhealthy'
            return Response(diagnostics, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        diagnostics['status'] = 'healthy'
        return Response(diagnostics, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def mobile_driver_registration(request):
    try:
        qr_data = request.data.get('qr_data', '')
        phone_number = request.data.get('phone_number', '')
        if not qr_data or not phone_number:
            return Response({'error': 'QR data and phone number required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            qr_info = json.loads(qr_data)
            truck_id = qr_info.get('truck_id')
        except json.JSONDecodeError:
            truck_id = qr_data

        try:
            truck = FleetTruck.objects.get(id=truck_id)
        except FleetTruck.DoesNotExist:
            return Response({'error': 'Truck not found'}, status=status.HTTP_404_NOT_FOUND)

        driver, created = FleetDriver.objects.get_or_create(
            phone_number=phone_number,
            defaults={'first_name': 'Driver', 'last_name': phone_number[-4:], 'email': f'driver_{phone_number}@fleet.local', 'fleet_id': truck.fleet_id}
        )
        driver.truck = truck
        driver.is_active = True
        driver.save()

        return Response({
            'driver_id': str(driver.id), 'truck_id': str(truck.id), 'driver_name': driver.get_display_name(),
            'truck_name': truck.truck_identifier, 'success': True
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def mobile_location_update(request):
    try:
        driver_id = request.data.get('driver_id')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        speed = request.data.get('speed', 0)
        
        if not driver_id or latitude is None or longitude is None:
            return Response({'error': 'driver_id, latitude, longitude required'}, status=status.HTTP_400_BAD_REQUEST)

        driver = FleetDriver.objects.get(id=driver_id)
        driver.latitude, driver.longitude, driver.current_speed = latitude, longitude, speed
        driver.save()

        if driver.truck:
            truck = driver.truck
            truck.last_latitude, truck.last_longitude, truck.speed_kmh = latitude, longitude, speed
            truck.save()
            
            active_mission = FleetMission.objects.filter(truck=truck, status='enroute').first()
            if active_mission:
                active_mission.current_location = {'lat': latitude, 'lon': longitude}
                active_mission.speed_kmh = speed
                active_mission.save()

        TruckLocation.objects.create(
            truck=driver.truck, driver=driver, latitude=latitude, longitude=longitude,
            speed=speed, timestamp=timezone.now()
        )

        if speed > 120:
            FleetActivity.objects.create(
                truck=driver.truck, driver=driver, activity_type='speed_violation',
                location_lat=latitude, location_lon=longitude, speed_kmh=speed,
                activity_date=timezone.now().date(), activity_time=timezone.now().time(), timestamp=timezone.now()
            )

        return Response({'success': True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def mobile_alert(request):
    try:
        driver_id = request.data.get('driver_id')
        alert_type = request.data.get('alert_type')
        message = request.data.get('message')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        driver = FleetDriver.objects.get(id=driver_id)
        FleetActivity.objects.create(
            truck=driver.truck, driver=driver, activity_type=alert_type,
            violation_details=message, location_lat=latitude, location_lon=longitude,
            activity_date=timezone.now().date(), activity_time=timezone.now().time(), timestamp=timezone.now()
        )
        return Response({'success': True}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def mobile_driver_profile(request, driver_id):
    try:
        driver = FleetDriver.objects.get(id=driver_id)
        current_mission = FleetMission.objects.filter(truck=driver.truck, status='enroute').first()
        return Response({
            'id': str(driver.id), 'name': driver.get_display_name(), 'phone': driver.phone_number,
            'performance_points': driver.performance_mark,
            'current_mission': {
                'id': str(current_mission.id), 'mission_number': current_mission.mission_number,
                'status': current_mission.status, 'origin': current_mission.origin, 'destination': current_mission.destination
            } if current_mission else None,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_missions(request, driver_id):
    try:
        driver = FleetDriver.objects.get(id=driver_id)
        missions = FleetMission.objects.filter(truck=driver.truck, status__in=['planned', 'assigned'])
        data = [{
            'id': str(m.id), 'mission_number': m.mission_number, 'status': m.status,
            'origin': m.origin, 'destination': m.destination, 'distance_total_m': float(m.distance_total_m)
        } for m in missions]
        return Response({'missions': data, 'total_count': len(data)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def start_mission_tracking(request):
    try:
        driver_id = request.data.get('driver_id')
        mission_id = request.data.get('mission_id')
        driver = FleetDriver.objects.get(id=driver_id)
        mission = FleetMission.objects.get(id=mission_id)
        
        mission.status = 'enroute'
        mission.driver = driver
        mission.started_at = timezone.now()
        mission.save()
        
        return Response({'success': True, 'mission_number': mission.mission_number}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
