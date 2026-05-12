

@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_missions(request, driver_id):
    """
    Get all available missions for a driver that are ready to start
    Filters by truck assignment and mission status
    """
    try:
        driver = FleetDriver.objects.get(id=driver_id)
        
        # Get driver's assigned truck
        truck = driver.truck
        if not truck:
            return Response(
                {'missions': [], 'message': 'Driver has not been assigned to a truck yet'},
                status=status.HTTP_200_OK
            )
        
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
                'distance_total_m': float(mission.distance_total_m),
                'cargo': mission.cargo if mission.cargo else {},
                'created_at': mission.created_at.isoformat() if mission.created_at else None,
            })
        
        return Response({
            'driver_id': str(driver.id),
            'driver_name': driver.get_display_name(),
            'truck_id': str(truck.id),
            'truck_name': truck.truck_identifier,
            'missions': missions_data,
            'total_count': len(missions_data)
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
        
        return Response({
            'success': True,
            'mission_id': str(mission.id),
            'mission_number': mission.mission_number,
            'status': mission.status,
            'origin': mission.origin,
            'destination': mission.destination,
            'driver_name': driver.get_display_name(),
            'tracking_id': str(mission.id),
            'message': f'Started tracking mission {mission.mission_number}'
        }, status=status.HTTP_200_OK)
        
    except FleetMission.DoesNotExist:
        return Response(
            {'error': 'Mission not found'},
            status=status.HTTP_404_NOT_FOUND
        )
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
