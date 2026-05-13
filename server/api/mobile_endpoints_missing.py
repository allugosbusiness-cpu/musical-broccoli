# Missing endpoints to add to server/api/mobile_endpoints.py

@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_missions(request, driver_id):
    """
    Get all available missions for a driver that are ready to start
    Filters by truck assignment and mission status
    Returns sample missions if driver doesn't exist (for testing)
    """
    try:
        driver = FleetDriver.objects.get(id=driver_id)
        
        # Get driver's assigned truck
        truck = driver.truck
        if not truck:
            return Response({
                'driver_id': str(driver.id),
                'driver_name': driver.get_display_name() if hasattr(driver, 'get_display_name') else f'{driver.first_name} {driver.last_name}',
                'truck_id': None,
                'truck_name': None,
                'missions': [],
                'total_count': 0,
                '_debug': 'Driver has not been assigned to a truck yet'
            }, status=status.HTTP_200_OK)
        
        # Get all PLANNED or ASSIGNED missions for this truck
        missions = FleetMission.objects.filter(
            truck=truck,
            status__in=['planned', 'assigned']
        ).order_by('-created_at')
        
        missions_data = []
        for mission in missions:
            missions_data.append({
                'id': str(mission.id),
                'mission_number': mission.mission_number,
                'status': mission.status,
                'origin': mission.origin if isinstance(mission.origin, dict) else {'lat': 0, 'lng': 0},
                'destination': mission.destination if isinstance(mission.destination, dict) else {'lat': 0, 'lng': 0},
                'distance_total_m': float(mission.distance_total_m) if mission.distance_total_m else 0,
                'cargo': mission.cargo if mission.cargo else {},
                'created_at': mission.created_at.isoformat() if mission.created_at else None,
            })
        
        driver_name = driver.get_display_name() if hasattr(driver, 'get_display_name') else f'{driver.first_name} {driver.last_name}'
        
        return Response({
            'driver_id': str(driver.id),
            'driver_name': driver_name,
            'truck_id': str(truck.id),
            'truck_name': truck.truck_identifier,
            'missions': missions_data,
            'total_count': len(missions_data),
            '_debug': f'Found {len(missions_data)} real missions from database'
        }, status=status.HTTP_200_OK)
        
    except FleetDriver.DoesNotExist:
        # Return sample missions for testing if driver doesn't exist
        sample_missions = [
            {
                'id': '00000000-0000-0000-0000-000000000001',
                'mission_number': 'TEST-MISSION-001',
                'status': 'planned',
                'origin': {'lat': 6.9271, 'lng': 33.7347},
                'destination': {'lat': 6.8, 'lng': 33.5},
                'distance_total_m': 12500,
                'cargo': {'item': 'Test cargo', 'weight_kg': 150},
                'created_at': timezone.now().isoformat(),
            },
            {
                'id': '00000000-0000-0000-0000-000000000002',
                'mission_number': 'TEST-MISSION-002',
                'status': 'planned',
                'origin': {'lat': 6.9271, 'lng': 33.7347},
                'destination': {'lat': 7.0, 'lng': 33.9},
                'distance_total_m': 18500,
                'cargo': {'item': 'Test supplies', 'weight_kg': 250},
                'created_at': timezone.now().isoformat(),
            },
        ]
        
        return Response({
            'driver_id': driver_id,
            'driver_name': 'Test Driver',
            'truck_id': 'test-truck',
            'truck_name': 'Test Vehicle',
            'missions': sample_missions,
            'total_count': len(sample_missions),
            '_note': 'Using sample data - driver not found in database'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def start_mission_tracking(request):
    """
    Start tracking for a mission
    Accepts either mission_id or mission_number
    """
    try:
        driver_id = request.data.get('driver_id')
        mission_id = request.data.get('mission_id')
        mission_number = request.data.get('mission_number')
        
        if not driver_id:
            return Response(
                {'error': 'driver_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find mission by ID or number
        mission = None
        if mission_id:
            mission = FleetMission.objects.get(id=mission_id)
        elif mission_number:
            mission = FleetMission.objects.get(mission_number=mission_number)
        else:
            return Response(
                {'error': 'mission_id or mission_number required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify driver has access to this mission
        driver = FleetDriver.objects.get(id=driver_id)
        if driver.truck != mission.truck:
            return Response(
                {'error': 'Driver is not assigned to this mission\'s truck'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Start the mission
        mission.status = 'enroute'
        mission.driver = driver
        mission.started_at = timezone.now()
        
        # ✅ FIXED: Initialize current_location to origin coordinates
        # This ensures the truck pin appears on the map when mission starts
        if mission.origin and not mission.current_location:
            mission.current_location = mission.origin
        
        mission.save()
        
        # Cache mission tracking session
        from django.core.cache import cache
        cache.set(f'mission_tracking_{mission.id}', {
            'mission_id': str(mission.id),
            'driver_id': str(driver.id),
            'truck_id': str(mission.truck.id),
            'started_at': timezone.now().isoformat(),
            'tracking_enabled': True
        }, timeout=None)
        
        driver_name = driver.get_display_name() if hasattr(driver, 'get_display_name') else f'{driver.first_name} {driver.last_name}'
        
        return Response({
            'success': True,
            'mission_id': str(mission.id),
            'mission_number': mission.mission_number,
            'status': mission.status,
            'origin': mission.origin,
            'destination': mission.destination,
            'driver_name': driver_name,
            'tracking_id': str(mission.id),
            'message': f'Started tracking mission {mission.mission_number}'
        }, status=status.HTTP_200_OK)
        
    except FleetMission.DoesNotExist:
        # For test missions, return mock tracking session
        import uuid
        tracking_id = str(uuid.uuid4())
        from django.core.cache import cache
        cache.set(f'mission_tracking_{tracking_id}', {
            'mission_id': mission_id or mission_number,
            'driver_id': driver_id,
            'truck_id': 'test-truck',
            'started_at': timezone.now().isoformat(),
            'tracking_enabled': True
        }, timeout=None)
        
        return Response({
            'success': True,
            'mission_id': mission_id or mission_number,
            'mission_number': mission_number or 'TEST-MISSION',
            'status': 'enroute',
            'origin': {'lat': 6.9271, 'lng': 33.7347},
            'destination': {'lat': 6.8, 'lng': 33.5},
            'driver_name': 'Test Driver',
            'tracking_id': tracking_id,
            'message': f'Started tracking mission {mission_number or mission_id}',
            '_note': 'Using test data - mission not found in database'
        }, status=status.HTTP_200_OK)
    except FleetDriver.DoesNotExist:
        return Response(
            {'error': 'Driver not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_debug_info(request):
    """
    Debug endpoint to check API availability and database connectivity
    """
    try:
        # Test database connectivity
        driver_count = FleetDriver.objects.count()
        truck_count = FleetTruck.objects.count()
        mission_count = FleetMission.objects.count()
        
        return Response({
            'status': 'ok',
            'timestamp': timezone.now().isoformat(),
            'database': {
                'connected': True,
                'drivers': driver_count,
                'trucks': truck_count,
                'missions': mission_count
            },
            'api_version': 'v1',
            'endpoints': {
                'available_missions': '/api/v1/mobile/driver/<driver_id>/available-missions/',
                'start_tracking': '/api/v1/mobile/mission/start-tracking/',
                'alert': '/api/v1/mobile/alert/',
                'current_mission': '/api/v1/mobile/driver/<driver_id>/current-mission/'
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e),
            'database': {
                'connected': False
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
