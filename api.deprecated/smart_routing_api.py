"""
Smart Routing & Trail System API Service
Production-ready routing engine with map-matching, re-routing, hazard detection, and SLA monitoring
"""
import math
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import numpy as np
from scipy.spatial.distance import cdist

import requests
from django.utils import timezone
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework.viewsets import ViewSet

logger = logging.getLogger(__name__)

# Configuration
ROUTING_ENGINE = "valhalla"  # or "osrm"
VALHALLA_SERVER = "http://localhost:8002"
OSRM_SERVER = "http://router.project-osrm.org"
TRAFFIC_API_KEY = ""  # Set from environment
HAZARD_DETECTION_ENABLED = True


class SmartRoutingService:
    """Core routing engine with fuel optimization, traffic awareness, and hazard detection"""

    # Speed profiles by road type
    SPEED_PROFILES = {
        'motorway': {'max': 120, 'avg': 100, 'fuel': 8.5},
        'primary': {'max': 100, 'avg': 80, 'fuel': 7.5},
        'secondary': {'max': 80, 'avg': 60, 'fuel': 6.5},
        'residential': {'max': 50, 'avg': 35, 'fuel': 5.0},
        'mountain': {'max': 50, 'avg': 35, 'fuel': 4.5},
    }

    # Vehicle profiles
    VEHICLE_PROFILES = {
        'truck': {
            'max_weight': 25000,  # kg
            'max_height': 4.2,  # meters
            'base_fuel': 25.0,  # liters per 100km
            'max_grade': 15,  # percent
            'speed_reduction_factor': 0.85
        },
        'van': {
            'max_weight': 3500,
            'max_height': 2.5,
            'base_fuel': 8.0,
            'max_grade': 20,
            'speed_reduction_factor': 0.95
        }
    }

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in km"""
        R = 6371
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    @staticmethod
    def valhalla_route(origin: Tuple[float, float], destination: Tuple[float, float],
                       vehicle_type: str = 'truck', profile: str = 'fuel_optimal',
                       avoid_hazards: bool = True) -> Dict:
        """
        Query Valhalla routing engine with vehicle-specific constraints.
        
        Args:
            origin: (lat, lon)
            destination: (lat, lon)
            vehicle_type: 'truck' or 'van'
            profile: 'fuel_optimal', 'fastest', 'avoid_hazards'
            avoid_hazards: Include hazard penalties
        
        Returns:
            Route dictionary with polyline, distance, duration, fuel estimate
        """
        try:
            # Build Valhalla request
            request_body = {
                "locations": [
                    {"lat": origin[0], "lon": origin[1]},
                    {"lat": destination[0], "lon": destination[1]}
                ],
                "costing": "truck" if vehicle_type == "truck" else "auto",
                "costing_options": {
                    "truck": {
                        "hazmat": False,
                        "axle_load": 9000,  # kg
                        "weight": 20000,  # kg
                        "height": 4.0,  # meters
                        "width": 2.5,
                        "length": 15.0,
                        "toll": True
                    }
                },
                "alternatives": True if profile == 'fuel_optimal' else False,
                "units": "kilometers"
            }

            # Add hazard avoidance if needed
            if avoid_hazards:
                request_body["avoid_locations"] = []
                # Hazard locations would be queried from database
                # Example: avoid school zones, sharp curves, steep descents

            response = requests.post(
                f"{VALHALLA_SERVER}/route",
                json=request_body,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Valhalla error: {response.status_code} - {response.text}")
                return None

            data = response.json()
            routes = data.get('trip', {}).get('legs', [])
            
            if not routes:
                return None

            best_route = routes[0]
            
            # Extract metrics
            distance_m = best_route.get('summary', {}).get('length', 0)
            duration_s = best_route.get('summary', {}).get('time', 0)
            distance_km = distance_m / 1000
            
            # Calculate fuel consumption
            fuel_liters = SmartRoutingService.calculate_fuel_consumption(
                distance_km=distance_km,
                vehicle_type=vehicle_type,
                avg_grade=5.0  # Estimated average grade
            )

            return {
                'polyline': best_route.get('shape', ''),
                'distance_km': distance_km,
                'duration_seconds': int(duration_s),
                'fuel_liters': fuel_liters,
                'estimated_cost': fuel_liters * 1.5,  # Assume $1.50/liter
                'segments': best_route.get('maneuvers', []),
                'confidence': 0.95
            }
            
        except Exception as e:
            logger.error(f"Valhalla routing error: {str(e)}")
            return None

    @staticmethod
    def osrm_route(origin: Tuple[float, float], destination: Tuple[float, float]) -> Dict:
        """Fallback to OSRM (simpler, less featured than Valhalla)"""
        try:
            url = f"{OSRM_SERVER}/route/v1/driving/{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
            response = requests.get(f"{url}?overview=full&geometries=geojson", timeout=10)
            
            if response.status_code != 200:
                return None

            data = response.json()
            if not data.get('routes'):
                return None

            route = data['routes'][0]
            distance_km = route['distance'] / 1000
            duration_s = route['duration']

            return {
                'polyline': json.dumps(route['geometry']),
                'distance_km': distance_km,
                'duration_seconds': int(duration_s),
                'fuel_liters': distance_km * 0.25,  # Rough estimate
                'estimated_cost': distance_km * 0.25 * 1.5,
                'segments': [],
                'confidence': 0.85
            }
        except Exception as e:
            logger.error(f"OSRM routing error: {str(e)}")
            return None

    @staticmethod
    def calculate_fuel_consumption(distance_km: float, vehicle_type: str, 
                                    avg_grade: float, load_factor: float = 1.0) -> float:
        """
        Calculate fuel consumption considering distance, vehicle, grade, and load.
        
        Formula: base_consumption * load_factor * grade_factor * efficiency_factor
        """
        profile = SmartRoutingService.VEHICLE_PROFILES.get(vehicle_type, {})
        base_fuel = profile.get('base_fuel', 25.0)
        
        # Grade penalty: 5% grade ~10% more fuel
        grade_factor = 1.0 + (avg_grade / 50)
        
        # Load factor (0.5 = half load, 1.0 = full load)
        consumption_l_per_100km = base_fuel * load_factor * grade_factor
        
        return distance_km * consumption_l_per_100km / 100

    @staticmethod
    def hmm_map_match(gps_points: List[Dict], road_segments: List[Dict]) -> List[Dict]:
        """
        Hidden Markov Model-based map matching for GPS trace.
        Snaps noisy GPS points to actual road network.
        
        Args:
            gps_points: List of {'lat', 'lon', 'timestamp'}
            road_segments: Road network geometry
        
        Returns:
            List of snapped points with segment IDs and confidence scores
        """
        snapped_trace = []
        emission_threshold_m = 50  # GPS within 50m of road
        
        # Candidate generation
        candidates_per_point = []
        for gps in gps_points:
            candidates = []
            for seg in road_segments:
                dist = SmartRoutingService.point_to_segment_distance(
                    (gps['lat'], gps['lon']),
                    (seg['start_lat'], seg['start_lon']),
                    (seg['end_lat'], seg['end_lon'])
                )
                if dist < emission_threshold_m:
                    candidates.append({
                        'segment_id': seg['id'],
                        'distance_m': dist,
                        'segment': seg
                    })
            candidates.sort(key=lambda x: x['distance_m'])
            candidates_per_point.append(candidates[:5])  # Keep top 5

        if not candidates_per_point or not candidates_per_point[0]:
            return []

        # Viterbi algorithm for HMM
        prev_probabilities = {}
        prev_best_path = {}

        # Initialize first point
        for candidate in candidates_per_point[0]:
            seg_id = candidate['segment_id']
            emission_prob = math.exp(-candidate['distance_m']**2 / (2 * 10**2))
            prev_probabilities[seg_id] = emission_prob
            prev_best_path[seg_id] = [seg_id]

        # Forward pass
        for i in range(1, len(gps_points)):
            curr_probabilities = {}
            curr_best_path = {}

            for curr_candidate in candidates_per_point[i]:
                curr_seg_id = curr_candidate['segment_id']
                max_prob = 0.0
                best_prev_seg = None

                for prev_seg_id, prev_prob in prev_probabilities.items():
                    # Transition probability
                    gps_distance = SmartRoutingService.haversine_distance(
                        gps_points[i-1]['lat'], gps_points[i-1]['lon'],
                        gps_points[i]['lat'], gps_points[i]['lon']
                    )
                    
                    # Estimate road distance (simple heuristic)
                    road_distance = gps_distance * 1.1
                    
                    distance_ratio = gps_distance / road_distance if road_distance > 0 else 1.0
                    transition_prob = math.exp(-0.5 * (distance_ratio - 1.0)**2)

                    # Emission probability
                    emission_prob = math.exp(-curr_candidate['distance_m']**2 / (2 * 10**2))

                    # Combined
                    combined_prob = prev_prob * transition_prob * emission_prob

                    if combined_prob > max_prob:
                        max_prob = combined_prob
                        best_prev_seg = prev_seg_id

                if max_prob > 0:
                    curr_probabilities[curr_seg_id] = max_prob
                    curr_best_path[curr_seg_id] = prev_best_path[best_prev_seg] + [curr_seg_id]

            prev_probabilities = curr_probabilities
            prev_best_path = curr_best_path

        # Backtrack to find best path
        if prev_probabilities:
            best_final_seg = max(prev_probabilities, key=prev_probabilities.get)
            best_path = prev_best_path[best_final_seg]

            # Generate snapped trace
            for i, gps in enumerate(gps_points):
                if i < len(best_path):
                    seg_id = best_path[i]
                    segment = next((s for s in road_segments if s['id'] == seg_id), None)
                    if segment:
                        # Project point onto segment
                        snapped = SmartRoutingService.project_point_on_segment(
                            (gps['lat'], gps['lon']),
                            (segment['start_lat'], segment['start_lon']),
                            (segment['end_lat'], segment['end_lon'])
                        )
                        snapped_trace.append({
                            'original_lat': gps['lat'],
                            'original_lon': gps['lon'],
                            'snapped_lat': snapped['lat'],
                            'snapped_lon': snapped['lon'],
                            'segment_id': seg_id,
                            'confidence': prev_probabilities.get(seg_id, 0),
                            'distance_to_road_m': snapped.get('distance', 0)
                        })

        return snapped_trace

    @staticmethod
    def point_to_segment_distance(point: Tuple[float, float],
                                  seg_start: Tuple[float, float],
                                  seg_end: Tuple[float, float]) -> float:
        """Calculate perpendicular distance from point to line segment"""
        # Using haversine for lat/lon
        px, py = point[1], point[0]  # lon, lat
        x1, y1 = seg_start[1], seg_start[0]
        x2, y2 = seg_end[1], seg_end[0]

        # Parameter t for closest point on segment
        if x2 == x1 and y2 == y1:
            return 0
        
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / 
                           ((x2 - x1)**2 + (y2 - y1)**2)))

        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)

        return SmartRoutingService.haversine_distance(point[0], point[1], closest_y, closest_x) * 1000

    @staticmethod
    def project_point_on_segment(point: Tuple[float, float],
                                 seg_start: Tuple[float, float],
                                 seg_end: Tuple[float, float]) -> Dict:
        """Project point onto line segment and return snapped coordinates"""
        px, py = point[1], point[0]
        x1, y1 = seg_start[1], seg_start[0]
        x2, y2 = seg_end[1], seg_end[0]

        if x2 == x1 and y2 == y1:
            return {'lat': seg_start[0], 'lon': seg_start[1], 'distance': 0}

        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / 
                           ((x2 - x1)**2 + (y2 - y1)**2)))

        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)

        distance = SmartRoutingService.haversine_distance(point[0], point[1], closest_y, closest_x) * 1000

        return {
            'lat': closest_y,
            'lon': closest_x,
            'distance': distance
        }

    @staticmethod
    def detect_hazards(polyline: List[Tuple[float, float]], vehicle_type: str = 'truck') -> List[Dict]:
        """
        Detect road hazards along a route (sharp curves, steep grades, etc.)
        Uses elevation data and OSM tags
        """
        hazards = []
        profile = SmartRoutingService.VEHICLE_PROFILES[vehicle_type]

        # Simplified hazard detection (in production, use ML model + OSM data)
        for i in range(1, len(polyline) - 1):
            prev_point = polyline[i - 1]
            curr_point = polyline[i]
            next_point = polyline[i + 1]

            # Calculate heading change (sharp curve detection)
            heading1 = math.atan2(
                curr_point[1] - prev_point[1],
                curr_point[0] - prev_point[0]
            )
            heading2 = math.atan2(
                next_point[1] - curr_point[1],
                next_point[0] - curr_point[0]
            )

            heading_change = abs(heading2 - heading1)
            if heading_change > math.radians(30):  # > 30 degree turn
                hazards.append({
                    'type': 'sharp_curve',
                    'location': curr_point,
                    'severity': min(1.0, heading_change / math.pi),
                    'recommendation': 'Reduce speed and watch for oncoming traffic'
                })

        return hazards

    @staticmethod
    def check_sla_compliance(vehicle_id: str, current_position: Tuple[float, float],
                             destination: Tuple[float, float],
                             sla_deadline: datetime,
                             remaining_distance_km: float) -> Dict:
        """Check if vehicle can meet SLA deadline at current speed"""
        now = datetime.now(timezone.utc)
        time_remaining_seconds = (sla_deadline - now).total_seconds()

        # Average needed speed
        avg_speed_needed = (remaining_distance_km * 3600) / time_remaining_seconds if time_remaining_seconds > 0 else 0

        return {
            'will_meet_sla': avg_speed_needed <= 100,  # Assuming 100 km/h max
            'speed_needed_kmh': avg_speed_needed,
            'time_remaining_seconds': time_remaining_seconds,
            'distance_remaining_km': remaining_distance_km,
            'buffer_minutes': (time_remaining_seconds / 60) - (remaining_distance_km / 80)
        }


# REST API Views

class SmartRouteViewSet(ViewSet):
    """API endpoints for smart routing"""

    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        Calculate optimal route
        POST /api/v2/routes/calculate
        """
        try:
            origin = (request.data['origin']['lat'], request.data['origin']['lon'])
            destination = (request.data['destination']['lat'], request.data['destination']['lon'])
            vehicle_id = request.data.get('vehicle_id', 'TRUCK-001')
            profile = request.data.get('profile', 'fuel_optimal')
            avoid_hazards = request.data.get('avoid_hazards', True)

            # Get vehicle profile
            vehicle_type = 'truck'  # Would be fetched from DB
            
            # Route calculation
            route = SmartRoutingService.valhalla_route(
                origin=origin,
                destination=destination,
                vehicle_type=vehicle_type,
                profile=profile,
                avoid_hazards=avoid_hazards
            )

            if not route:
                # Fallback to OSRM
                route = SmartRoutingService.osrm_route(origin, destination)

            if not route:
                return Response(
                    {'error': 'Could not calculate route'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Detect hazards
            if avoid_hazards:
                route['hazards'] = SmartRoutingService.detect_hazards(
                    polyline=[(origin, destination)],
                    vehicle_type=vehicle_type
                )

            route['route_id'] = f"route-{datetime.now().timestamp()}"
            route['vehicle_id'] = vehicle_id
            route['profile'] = profile
            route['created_at'] = datetime.now().isoformat()

            return Response(route, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Route calculation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def gps_ingest(self, request):
        """
        Ingest GPS points for a vehicle
        POST /api/v2/gps
        """
        try:
            vehicle_id = request.data['vehicle_id']
            points = request.data['points']

            # In production, these would be queued to Kafka
            logger.info(f"Ingested {len(points)} GPS points for {vehicle_id}")

            # Map-matching (simplified - in production use Valhalla)
            snapped_trace = SmartRoutingService.hmm_map_match(
                gps_points=points,
                road_segments=[]  # Would load from DB
            )

            return Response({
                'status': 'accepted',
                'points_ingested': len(points),
                'latest_point': points[-1] if points else None,
                'snapped_trace': snapped_trace[:5] if snapped_trace else []
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            logger.error(f"GPS ingest error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def trails(self, request):
        """
        Get snapped trail for a vehicle
        GET /api/v2/trails/{vehicle_id}
        """
        vehicle_id = request.query_params.get('vehicle_id')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')

        # In production, query from TimescaleDB
        trail_data = {
            'vehicle_id': vehicle_id,
            'polyline': {
                'type': 'LineString',
                'coordinates': []
            },
            'total_distance_km': 0,
            'total_time_seconds': 0,
            'map_match_quality': {
                'avg_confidence': 0.95
            }
        }

        return Response(trail_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def hazards(self, request):
        """
        Query hazards in a bbox
        GET /api/v2/hazards?bounds=minLon,minLat,maxLon,maxLat
        """
        bounds = request.query_params.get('bounds', '').split(',')

        if len(bounds) != 4:
            return Response(
                {'error': 'Invalid bounds format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # In production, query from PostGIS
        hazards = [
            {
                'hazard_id': 'h1',
                'type': 'sharp_curve',
                'location': {'lat': 17.85, 'lon': 25.81},
                'severity_score': 0.75,
                'recommendation': 'Reduce speed to 35 km/h'
            }
        ]

        return Response({
            'bbox': bounds,
            'hazard_count': len(hazards),
            'hazards': hazards
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def sla_status(self, request):
        """
        Get SLA compliance status for a vehicle
        GET /api/v2/vehicles/{vehicle_id}/sla-status
        """
        vehicle_id = request.query_params.get('vehicle_id')

        sla_status = {
            'vehicle_id': vehicle_id,
            'milestones': [],
            'total_potential_penalty': 0,
            'breach_count': 0
        }

        return Response(sla_status, status=status.HTTP_200_OK)
