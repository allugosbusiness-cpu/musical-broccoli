from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Truck, Checkpoint, Cargo, Alert, KPI, Route, TrackPoint, AlertType, Location, CurrentLocation, RouteOptimization
from .serializers import (
    TruckSerializer, TruckListSerializer, CheckpointSerializer,
    CargoSerializer, AlertSerializer, KPISerializer, RouteSerializer, TrackPointSerializer,
    LocationSerializer, CurrentLocationSerializer, RouteOptimizationSerializer
)
from .routing_service import RoutingService
# from .ml_optimizer import get_route_optimizer  # TODO: Fix numpy dependency for Python 3.14
from .osrm_service import compute_route_geometry
from .color_utils import generate_truck_color

# Stub for get_route_optimizer to work around numpy installation issue
def get_route_optimizer():
    return None

class TruckViewSet(viewsets.ModelViewSet):
    queryset = Truck.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'location']
    search_fields = ['plate', 'driver', 'location']
    ordering_fields = ['id', 'speed', 'progress', 'last_updated']
    ordering = ['-last_updated']

    def perform_create(self, serializer):
        """
        Override create to compute route geometry and assign truck color
        Accepts origin/destination as {lat, lng} coordinates in request
        """
        # Save truck first to get ID for color generation
        truck = serializer.save()
        
        # Generate and assign unique color for this truck
        truck_color = generate_truck_color(str(truck.id))
        truck.route_color = truck_color
        
        # If origin and destination coordinates provided, compute route
        try:
            origin = truck.origin_coordinates
            destination = truck.destination_coordinates
            
            if origin and destination:
                origin_lat = origin.get('lat')
                origin_lng = origin.get('lng')
                dest_lat = destination.get('lat')
                dest_lng = destination.get('lng')
                
                if all([origin_lat, origin_lng, dest_lat, dest_lng]):
                    # Call OSRM to compute route geometry
                    route_data = compute_route_geometry(
                        origin_lat, origin_lng,
                        dest_lat, dest_lng,
                        waypoints=[]
                    )
                    
                    if route_data and 'geometry' in route_data:
                        # Store GeoJSON geometry in truck
                        truck.route_geojson = route_data['geometry']
        except Exception as e:
            # Log error but don't fail truck creation
            print(f"⚠️ Error computing route for truck {truck.id}: {str(e)}")
        
        # Save truck with color and route geometry
        truck.save()

    def get_serializer_class(self):
        if self.action == 'list':
            return TruckListSerializer
        return TruckSerializer

    @action(detail=True, methods=['get'])
    def checkpoints(self, request, pk=None):
        """Get all checkpoints for a specific truck"""
        truck = self.get_object()
        checkpoints = truck.checkpoints.all()
        serializer = CheckpointSerializer(checkpoints, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def alerts(self, request, pk=None):
        """Get all alerts for a specific truck"""
        truck = self.get_object()
        alerts = truck.alerts.filter(is_resolved=False)
        serializer = AlertSerializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update truck status"""
        truck = self.get_object()
        truck.status = request.data.get('status', truck.status)
        truck.location = request.data.get('location', truck.location)
        truck.speed = request.data.get('speed', truck.speed)
        truck.progress = request.data.get('progress', truck.progress)
        truck.save()
        serializer = self.get_serializer(truck)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generate_routes(self, request):
        """
        Auto-generate routes for all trucks with origin/destination set
        Optional: ?truck_id=TRUCK-001 to generate for single truck
        """
        from api.data_locations import GLOBAL_LOCATIONS
        
        truck_id = request.query_params.get('truck_id')
        
        if truck_id:
            # Generate for single truck
            try:
                truck = Truck.objects.get(id=truck_id)
                trucks = [truck]
            except Truck.DoesNotExist:
                return Response(
                    {'error': f'Truck {truck_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Generate for all trucks with auto-routing enabled and no current route
            trucks = Truck.objects.filter(
                auto_routing_enabled=True,
                current_route__isnull=True
            ).exclude(origin='', destination='')
        
        created_routes = []
        errors = []
        
        for truck in trucks:
            try:
                origin_loc = GLOBAL_LOCATIONS.get(truck.origin)
                dest_loc = GLOBAL_LOCATIONS.get(truck.destination)
                
                if not origin_loc or not dest_loc:
                    errors.append(f"Invalid location for {truck.plate}: {truck.origin} → {truck.destination}")
                    continue
                
                origin_coords = {'lat': origin_loc['lat'], 'lng': origin_loc['lng']}
                dest_coords = {'lat': dest_loc['lat'], 'lng': dest_loc['lng']}
                
                # Create optimized route
                route = RoutingService.create_optimized_route(
                    truck.id,
                    truck.origin,
                    truck.destination,
                    origin_coords,
                    dest_coords
                )
                
                # Set as current route
                truck.current_route = route
                truck.origin_coordinates = origin_coords
                truck.destination_coordinates = dest_coords
                truck.save()
                
                created_routes.append({
                    'truck_id': truck.id,
                    'route_id': str(route.id),
                    'distance_km': route.distance_km,
                    'duration_hours': route.estimated_duration_hours
                })
            except Exception as e:
                errors.append(f"Error generating route for {truck.plate}: {str(e)}")
        
        return Response({
            'created_routes': len(created_routes),
            'routes': created_routes,
            'errors': errors
        })
    
    @action(detail=True, methods=['patch'])
    def update_location(self, request, pk=None):
        """
        Update truck location and coordinates in real-time
        Used by driver mobile app
        """
        truck = self.get_object()
        
        # Update location
        if 'location' in request.data:
            truck.location = request.data['location']
        if 'coordinates' in request.data:
            truck.coordinates = request.data['coordinates']
        if 'speed' in request.data:
            truck.speed = request.data['speed']
        if 'progress' in request.data:
            truck.progress = request.data['progress']
        if 'distance_travelled' in request.data:
            truck.distance_travelled = request.data['distance_travelled']
        
        truck.save()
        
        # Update route progress if active route exists
        if truck.current_route and truck.current_route.status == 'in_progress':
            distance_travelled = request.data.get('distance_travelled', truck.distance_travelled)
            time_elapsed = request.data.get('time_elapsed_hours', 0)
            waypoint_index = request.data.get('current_waypoint_index', truck.current_route.current_waypoint_index)
            
            RoutingService.update_route_progress(
                truck.current_route.id,
                distance_travelled,
                time_elapsed,
                waypoint_index
            )
        
        serializer = self.get_serializer(truck)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def truck_trail(self, request, pk=None):
        """
        Get historical GPS trail showing where the truck has been
        Returns chronologically ordered track points
        """
        truck = self.get_object()
        limit = int(request.query_params.get('limit', 100))
        
        trail = RoutingService.get_truck_trail(truck.id, limit=limit)
        
        return Response({
            'truck_id': truck.id,
            'truck_plate': truck.plate,
            'trail_points': trail,
            'total_points': len(trail),
        })
    
    @action(detail=True, methods=['get'])
    def truck_trail_with_directions(self, request, pk=None):
        """
        Get truck trail snapped to roads with turn-by-turn directions
        Google Maps style with actual road following
        """
        truck = self.get_object()
        limit = int(request.query_params.get('limit', 200))
        
        trail_data = RoutingService.get_truck_trail_with_directions(truck.id, limit=limit)
        
        if not trail_data:
            return Response(
                {'error': 'No trail data available'},
                status=status.HTTP_204_NO_CONTENT
            )
        
        return Response(trail_data)
    
    @action(detail=True, methods=['post'])
    def route(self, request, pk=None):
        """
        POST endpoint to match GPS points to roads and update truck route
        Frontend calls this with buffered GPS points to snap to OSRM geometry
        
        Request body:
        {
          "gps_points": [
            {"lat": -17.8252, "lng": 31.0335},
            {"lat": -17.8260, "lng": 31.0345},
            ...
          ]
        }
        
        Response:
        {
          "route_geojson": {
            "type": "LineString",
            "coordinates": [[31.0335, -17.8252], [31.0345, -17.8260], ...]
          },
          "route_color": "#C81C50"
        }
        """
        truck = self.get_object()
        gps_points = request.data.get('gps_points', [])
        
        # Validate minimum points
        if not gps_points or len(gps_points) < 2:
            return Response(
                {'error': 'At least 2 GPS points required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Convert gps_points to OSRM format [(lng, lat), ...]
            coordinates = []
            for point in gps_points:
                lat = point.get('lat')
                lng = point.get('lng')
                if lat is not None and lng is not None:
                    coordinates.append([lng, lat])
            
            if len(coordinates) < 2:
                return Response(
                    {'error': 'Invalid GPS point format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Call OSRM /match endpoint to snap GPS trace to roads
            matched_geojson = self._match_gps_trace(coordinates)
            
            if not matched_geojson or not matched_geojson.get('geometry'):
                # Return error - never use straight line polyline as final
                return Response(
                    {'error': 'OSRM could not match GPS trace to roads'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Store matched geometry in truck
            truck.route_geojson = matched_geojson.get('geometry')
            truck.save()
            
            # Return matched geometry and truck color for frontend rendering
            return Response({
                'route_geojson': truck.route_geojson,
                'route_color': truck.route_color or '#0066cc',
                'matched': True
            })
            
        except Exception as e:
            return Response(
                {'error': f'Route matching failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _match_gps_trace(self, coordinates):
        """
        Call OSRM /match endpoint to snap GPS coordinates to roads
        Converts GeoJSON response to FeatureCollection compatible format
        
        Args:
            coordinates: List of [lng, lat] tuples
        
        Returns:
            dict with 'geometry' key containing LineString geometry
        """
        import requests
        
        if not coordinates or len(coordinates) < 2:
            return None
        
        # Prepare OSRM request
        # Sample to max 100 points to avoid massive requests
        if len(coordinates) > 100:
            step = len(coordinates) // 100
            sampled_coords = coordinates[::step]
            if sampled_coords[-1] != coordinates[-1]:
                sampled_coords.append(coordinates[-1])
            coordinates = sampled_coords
        
        # Format: lng,lat;lng,lat;...
        coord_string = ';'.join([f'{lng},{lat}' for lng, lat in coordinates])
        
        url = f'https://router.project-osrm.org/match/v1/driving/{coord_string}'
        params = {
            'geometries': 'geojson',
            'overview': 'full',
            'steps': 'false',
            'gaps': 'split',
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == 'Ok' and data.get('matchings'):
                # Return first matching (usually most accurate)
                matching = data['matchings'][0]
                return {
                    'geometry': matching.get('geometry', {}),
                    'confidence': matching.get('confidence', 0),
                    'legs': matching.get('legs', [])
                }
            
            return None
            
        except requests.exceptions.Timeout:
            print(f"⚠️ OSRM /match timeout for {len(coordinates)} points")
            return None
        except Exception as e:
            print(f"❌ OSRM /match error: {str(e)}")
            return None
    
    @action(detail=True, methods=['get'])
    def quick_routes(self, request, pk=None):
        """
        Get smart alternative route suggestions
        Shows fastest, balanced, and scenic routes from current position to destination
        """
        truck = self.get_object()
        
        # Validate truck has destination
        if not truck.destination_coordinates:
            return Response(
                {'error': 'Truck destination coordinates not set'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get current truck position (or use origin if just starting)
        current_coords = truck.coordinates or truck.origin_coordinates
        if not current_coords:
            return Response(
                {'error': 'Truck location coordinates not available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get quick routes
        routes = RoutingService.get_quick_routes(
            current_coords,
            truck.destination_coordinates,
            num_routes=3
        )
        
        return Response({
            'truck_id': truck.id,
            'truck_plate': truck.plate,
            'current_location': current_coords,
            'destination': truck.destination_coordinates,
            'suggested_routes': routes,
            'total_routes': len(routes),
        })
    
    @action(detail=True, methods=['post'])
    def record_position(self, request, pk=None):
        """
        Record a GPS track point for the truck
        Called periodically to build historical trail data
        """
        truck = self.get_object()
        
        # Validate required fields
        if 'latitude' not in request.data or 'longitude' not in request.data:
            return Response(
                {'error': 'latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Record the track point
        track_point = RoutingService.record_truck_position(
            truck_id=truck.id,
            latitude=float(request.data['latitude']),
            longitude=float(request.data['longitude']),
            speed=float(request.data.get('speed', 0)),
            heading=float(request.data.get('heading')) if 'heading' in request.data else None,
            altitude=float(request.data.get('altitude')) if 'altitude' in request.data else None,
            accuracy=float(request.data.get('accuracy')) if 'accuracy' in request.data else None,
            route_id=request.data.get('route_id'),
        )
        
        if track_point:
            serializer = TrackPointSerializer(track_point)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': 'Failed to record position'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def all_trucks_with_trails(self, request):
        """
        Get all trucks with their real-time trail data
        Returns trucks with current location and historical GPS trails
        For real-time map display on frontend
        """
        trucks = self.get_queryset()
        trucks_data = []
        
        for truck in trucks:
            # Get truck basic data
            truck_data = TruckListSerializer(truck).data
            
            # Get current trail
            trail = RoutingService.get_truck_trail(truck.id, limit=50)
            truck_data['trail'] = trail
            
            # Add origin/destination info
            truck_data['origin'] = truck.origin
            truck_data['destination'] = truck.destination
            truck_data['origin_coordinates'] = truck.origin_coordinates
            truck_data['destination_coordinates'] = truck.destination_coordinates
            
            trucks_data.append(truck_data)
        
        return Response({
            'trucks': trucks_data,
            'total': len(trucks_data),
            'timestamp': timezone.now()
        })
    
    @action(detail=True, methods=['post'])
    def record_gps_position(self, request, pk=None):
        """
        Record real-time GPS position from driver mobile app
        Accepts: latitude, longitude, speed, heading, altitude, accuracy
        Returns: TrackPoint data
        """
        truck = self.get_object()
        
        # Validate required fields
        required_fields = ['latitude', 'longitude']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            latitude = float(request.data['latitude'])
            longitude = float(request.data['longitude'])
            speed = float(request.data.get('speed', 0))
            heading = float(request.data.get('heading')) if 'heading' in request.data else None
            altitude = float(request.data.get('altitude')) if 'altitude' in request.data else None
            accuracy = float(request.data.get('accuracy')) if 'accuracy' in request.data else None
            
            # Create track point
            track_point = TrackPoint.objects.create(
                truck=truck,
                latitude=latitude,
                longitude=longitude,
                speed=speed,
                heading=heading,
                altitude=altitude,
                accuracy=accuracy,
                recorded_at=timezone.now()
            )
            
            # Update truck current location
            truck.coordinates = {'lat': latitude, 'lng': longitude}
            truck.speed = speed
            truck.save()
            
            # Check for speed violations (overspeeding)
            SPEED_LIMIT = 120  # km/h
            if speed > SPEED_LIMIT:
                # Create alert for overspeeding
                Alert.objects.create(
                    truck=truck,
                    alert_type='warning',
                    message=f"Overspeeding detected: {speed} km/h (limit: {SPEED_LIMIT} km/h)",
                    driver_name=truck.driver
                )
            
            serializer = TrackPointSerializer(track_point)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except (ValueError, TypeError) as e:
            return Response(
                {'error': f'Invalid data format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def calculate_optimal_route(self, request):
        """
        Calculate an optimal route with road-following navigation
        """
        from api.data_locations import GLOBAL_LOCATIONS
        
        truck_id = request.data.get('truck_id')
        destination = request.data.get('destination')
        current_location = request.data.get('current_location')
        
        if not truck_id or not destination:
            return Response(
                {'error': 'truck_id and destination are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            truck = Truck.objects.get(id=truck_id)
        except Truck.DoesNotExist:
            return Response(
                {'error': f'Truck {truck_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get coordinates
        if current_location:
            origin_coords = current_location
        else:
            origin_loc = GLOBAL_LOCATIONS.get(truck.origin) or GLOBAL_LOCATIONS.get(truck.location)
            if not origin_loc:
                return Response(
                    {'error': 'Could not determine truck starting location'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            origin_coords = {'lat': origin_loc['lat'], 'lng': origin_loc['lng']}
        
        dest_loc = GLOBAL_LOCATIONS.get(destination)
        if not dest_loc:
            return Response(
                {'error': f'Destination "{destination}" not found in locations database'},
                status=status.HTTP_400_BAD_REQUEST
            )
        dest_coords = {'lat': dest_loc['lat'], 'lng': dest_loc['lng']}
        
        # Get OSRM route (road-following)
        osrm_route = RoutingService.get_osrm_route(origin_coords, dest_coords)
        
        # Get quick routes
        quick_routes = RoutingService.get_quick_routes(origin_coords, dest_coords)
        
        return Response({
            'truck_id': truck.id,
            'origin': truck.origin,
            'destination': destination,
            'primary_route': osrm_route,
            'alternative_routes': quick_routes,
        })

class CheckpointViewSet(viewsets.ModelViewSet):
    queryset = Checkpoint.objects.all()
    serializer_class = CheckpointSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['truck', 'status']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['truck', 'cargo_type']
    search_fields = ['origin', 'destination', 'description']

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['truck', 'alert_type', 'is_resolved']
    ordering = ['-timestamp']
    
    def create(self, request, *args, **kwargs):
        """Override create to prevent duplicate alerts within 5 seconds"""
        from django.utils import timezone
        from datetime import timedelta
        
        truck_id = request.data.get('truck')
        alert_type = request.data.get('alert_type')
        
        if truck_id and alert_type:
            # Check if identical unresolved alert exists within last 5 seconds
            recent_alert = Alert.objects.filter(
                truck_id=truck_id,
                alert_type=alert_type,
                is_resolved=False,
                timestamp__gte=timezone.now() - timedelta(seconds=5)
            ).first()
            
            if recent_alert:
                # Return existing alert instead of creating duplicate
                serializer = self.get_serializer(recent_alert)
                return Response(serializer.data, status=status.HTTP_200_OK)
        
        # No duplicate found, create new alert
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def calculate_kpis(self, request):
        """
        Calculate key performance indicators from real-time database
        Returns: active trucks, on-time rate, avg speed, deliveries, speed violations, critical alerts
        """
        # Import FleetTruck model
        from .models_v2 import FleetTruck
        from django.utils import timezone
        
        trucks = FleetTruck.objects.all()
        alerts = Alert.objects.all()
        
        # Count metrics
        total_trucks = trucks.count()
        # Count trucks that are ENROUTE (equivalent to active/moving)
        active_trucks = trucks.filter(status='ENROUTE').count()
        # Count trucks with IDLE status as "delivered" analogue
        idle_trucks = trucks.filter(status='IDLE').count()
        
        # Calculate average speed from all trucks (simplified since FleetTruck doesn't have speed field)
        avg_speed = 0  # Placeholder - would need TruckLocation data for this
        
        # Use idle trucks as on-time deliveries analogue
        on_time_rate = (idle_trucks / total_trucks * 100) if total_trucks > 0 else 0
        
        # Speed violations (unresolved alerts of type warning/critical with speed-related messages)
        speed_violations = alerts.filter(
            alert_type__in=['warning', 'critical'],
            is_resolved=False,
            message__icontains='speed'
        ).count()
        
        # Critical alerts (unresolved)
        critical_alerts = alerts.filter(
            alert_type='critical',
            is_resolved=False
        ).count()
        
        return Response({
            'timestamp': timezone.now(),
            'metrics': {
                'active_trucks': active_trucks,
                'total_trucks': total_trucks,
                'on_time_rate': round(on_time_rate, 2),
                'avg_speed': round(avg_speed, 2),
                'total_deliveries': idle_trucks,
                'speed_violations': speed_violations,
                'critical_alerts': critical_alerts
            }
        })

    @action(detail=True, methods=['patch'])
    def resolve(self, request, pk=None):
        """Mark an alert as resolved"""
        alert = self.get_object()
        alert.is_resolved = True
        from django.utils import timezone
        alert.resolved_at = timezone.now()
        alert.save()
        serializer = self.get_serializer(alert)
        return Response(serializer.data)

class KPIViewSet(viewsets.ModelViewSet):
    queryset = KPI.objects.all()
    serializer_class = KPISerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['date', 'timestamp']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get the latest KPI metrics"""
        latest_kpi = KPI.objects.latest('timestamp')
        serializer = self.get_serializer(latest_kpi)
        return Response(serializer.data)

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['truck', 'status', 'origin', 'destination']
    search_fields = ['origin', 'destination', 'truck__plate', 'truck__driver']
    ordering_fields = ['created_at', 'distance_km', 'optimization_score']
    ordering = ['-created_at']

    @action(detail=False, methods=['post'])
    def create_optimized_route(self, request):
        """
        Create optimized route for a truck
        Expected POST data:
        {
            "truck_id": "T001",
            "origin": "Harare",
            "destination": "Bulawayo",
            "origin_coordinates": {"lat": -17.8252, "lng": 31.0335},
            "destination_coordinates": {"lat": -20.1550, "lng": 28.5795}
        }
        """
        try:
            truck_id = request.data.get('truck_id')
            origin = request.data.get('origin')
            destination = request.data.get('destination')
            origin_coords = request.data.get('origin_coordinates')
            destination_coords = request.data.get('destination_coordinates')
            
            if not all([truck_id, origin, destination, origin_coords, destination_coords]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            route = RoutingService.create_optimized_route(
                truck_id, origin, destination, origin_coords, destination_coords
            )
            
            serializer = self.get_serializer(route)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def active_routes(self, request):
        """Get all active routes"""
        routes = RoutingService.get_active_routes()
        serializer = self.get_serializer(routes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def truck_routes(self, request):
        """Get all routes for a specific truck"""
        truck_id = request.query_params.get('truck_id')
        
        if not truck_id:
            return Response(
                {'error': 'truck_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        routes = RoutingService.get_truck_routes(truck_id)
        serializer = self.get_serializer(routes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_progress(self, request, pk=None):
        """Update route progress"""
        try:
            distance_travelled = request.data.get('distance_travelled_km', 0)
            time_elapsed = request.data.get('time_elapsed_hours', 0)
            waypoint_index = request.data.get('current_waypoint_index', 0)
            
            route = RoutingService.update_route_progress(
                pk, distance_travelled, time_elapsed, waypoint_index
            )
            
            serializer = self.get_serializer(route)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['patch'])
    def start_route(self, request, pk=None):
        """Start a route (change status from planned to in_progress)"""
        try:
            route = self.get_object()
            
            if route.status != 'planned':
                return Response(
                    {'error': f'Route must be in planned status to start (current: {route.status})'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            route.status = 'in_progress'
            route.started_at = timezone.now()
            route.save()
            
            serializer = self.get_serializer(route)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class LocationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing locations (origins, destinations, checkpoints)"""
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['location_type']
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'congestion_factor']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get locations filtered by type"""
        location_type = request.query_params.get('type')
        if not location_type:
            return Response(
                {'error': 'type parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        locations = Location.objects.filter(location_type=location_type)
        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def trucks_starting(self, request, pk=None):
        """Get all trucks starting from this location"""
        location = self.get_object()
        trucks = location.trucks_starting_here.all()
        serializer = TruckListSerializer(trucks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def trucks_going(self, request, pk=None):
        """Get all trucks heading to this location"""
        location = self.get_object()
        trucks = location.trucks_going_here.all()
        serializer = TruckListSerializer(trucks, many=True)
        return Response(serializer.data)


class CurrentLocationViewSet(viewsets.ViewSet):
    """ViewSet for managing current truck locations with ML predictions"""
    
    def list(self, request):
        """Get current locations of all trucks"""
        current_locs = CurrentLocation.objects.all()
        serializer = CurrentLocationSerializer(current_locs, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get current location of a specific truck"""
        try:
            current_loc = CurrentLocation.objects.get(truck_id=pk)
            serializer = CurrentLocationSerializer(current_loc)
            return Response(serializer.data)
        except CurrentLocation.DoesNotExist:
            return Response(
                {'error': f'Current location not found for truck {pk}'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def update_current_location(self, request):
        """Update current location of a truck with ML predictions"""
        truck_id = request.data.get('truck_id')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        speed = request.data.get('speed', 0)
        
        if not all([truck_id, latitude, longitude]):
            return Response(
                {'error': 'truck_id, latitude, longitude required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            truck = Truck.objects.get(id=truck_id)
            
            # Get or create current location
            current_loc, created = CurrentLocation.objects.get_or_create(
                truck=truck,
                defaults={
                    'latitude': latitude,
                    'longitude': longitude,
                    'speed': speed,
                    'recorded_at': timezone.now()
                }
            )
            
            if not created:
                # Update existing location
                current_loc.latitude = latitude
                current_loc.longitude = longitude
                current_loc.speed = speed
                current_loc.recorded_at = timezone.now()
            
            # ML predictions: estimate fuel, ETA, next location
            optimizer = get_route_optimizer()
            
            if optimizer and truck.destination_coordinates:
                dest = truck.destination_coordinates
                distance_km = optimizer.haversine_distance(
                    (latitude, longitude),
                    (dest.get('lat'), dest.get('lng'))
                )
                
                # Predict ETA
                eta_data = optimizer.predict_eta(
                    {'lat': latitude, 'lng': longitude},
                    dest,
                    distance_km
                )
                
                current_loc.predicted_arrival_time = timezone.now() + \
                    timezone.timedelta(hours=eta_data['time_hours'])
                current_loc.distance_to_destination_km = distance_km
                current_loc.time_to_destination_minutes = eta_data['time_hours'] * 60
                current_loc.predicted_fuel_consumption_liters = optimizer.estimate_fuel_consumption(distance_km)
            
            current_loc.save()
            
            serializer = CurrentLocationSerializer(current_loc)
            return Response(serializer.data)
        
        except Truck.DoesNotExist:
            return Response(
                {'error': f'Truck {truck_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RouteOptimizationViewSet(viewsets.ViewSet):
    """ViewSet for ML-based route optimization results"""
    
    def list(self, request):
        """Get all route optimizations"""
        optimizations = RouteOptimization.objects.all()
        serializer = RouteOptimizationSerializer(optimizations, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get optimization for a specific route"""
        try:
            optimization = RouteOptimization.objects.get(route_id=pk)
            serializer = RouteOptimizationSerializer(optimization)
            return Response(serializer.data)
        except RouteOptimization.DoesNotExist:
            return Response(
                {'error': f'Optimization not found for route {pk}'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def optimize_route(self, request):
        """Generate route optimization using ML"""
        route_id = request.data.get('route_id')
        
        if not route_id:
            return Response(
                {'error': 'route_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            route = Route.objects.get(id=route_id)
            optimizer = get_route_optimizer()
            
            if not optimizer:
                return Response(
                    {'error': 'ML optimizer unavailable (numpy dependency issue). Please install numpy or use basic routing.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Calculate distances
            origin = route.origin_coordinates
            dest = route.destination_coordinates
            waypoints = route.waypoints or []
            
            original_distance = optimizer.calculate_route_distance(
                [origin] + waypoints + [dest]
            )
            
            # Optimize waypoint order
            optimized_waypoints = optimizer.optimize_waypoints_order(origin, waypoints, dest)
            optimized_distance = optimizer.calculate_route_distance(
                [origin] + optimized_waypoints + [dest]
            )
            
            # Calculate time savings
            original_time = optimizer.estimate_time(original_distance)
            optimized_time = optimizer.estimate_time(optimized_distance)
            
            # Calculate fuel metrics
            fuel_liters = optimizer.estimate_fuel_consumption(optimized_distance)
            co2_kg = optimizer.calculate_co2_emissions(fuel_liters)
            
            # Calculate optimization score
            score = optimizer.calculate_optimization_score(
                original_distance, optimized_distance,
                original_time, optimized_time
            )
            
            # Generate alternatives
            alternatives = optimizer.generate_alternative_routes(
                origin, dest, waypoints
            )
            
            # Create or update optimization
            optimization, created = RouteOptimization.objects.update_or_create(
                route=route,
                defaults={
                    'truck': route.truck,
                    'original_distance_km': original_distance,
                    'optimized_distance_km': optimized_distance,
                    'distance_saved_percent': ((original_distance - optimized_distance) / original_distance * 100) if original_distance > 0 else 0,
                    'original_time_hours': original_time,
                    'optimized_time_hours': optimized_time,
                    'time_saved_percent': ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0,
                    'estimated_fuel_liters': fuel_liters,
                    'fuel_cost_estimated': fuel_liters * 2.5,  # Assuming $2.50/liter
                    'co2_emissions_kg': co2_kg,
                    'alternative_routes': alternatives,
                    'confidence_score': 0.85,
                    'reasoning': f'Optimized route saves {(original_distance - optimized_distance):.1f}km and {(original_time - optimized_time):.1f} hours'
                }
            )
            
            serializer = RouteOptimizationSerializer(optimization)
            return Response(serializer.data)
        
        except Route.DoesNotExist:
            return Response(
                {'error': f'Route {route_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['patch'])
    def complete_route(self, request, pk=None):
        """Complete a route"""
        try:
            route = self.get_object()
            
            route.status = 'completed'
            route.completed_at = timezone.now()
            route.distance_travelled_km = route.distance_km
            route.time_elapsed_hours = route.estimated_duration_hours
            route.save()
            
            serializer = self.get_serializer(route)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
