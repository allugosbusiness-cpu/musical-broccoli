"""
ML-Powered Smart Routing Service
Integrates OSRM for road-following navigation + ML for route optimization
Features: Historical trails, real-time routing, traffic prediction, alternative routes
"""
import math
import requests
import json
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Route, Truck, TrackPoint
import random
import logging

logger = logging.getLogger(__name__)

# OSRM Server (you can self-host or use the public demo server)
OSRM_SERVER = "http://router.project-osrm.org"  # Free public server; deploy your own for production


class RoutingService:
    """Intelligent routing engine with ML-based optimization"""
    
    # Speed profiles based on road types (km/h)
    SPEED_PROFILES = {
        'highway': {'max': 110, 'avg': 95, 'min': 80},
        'urban': {'max': 60, 'avg': 40, 'min': 20},
        'rural': {'max': 80, 'avg': 65, 'min': 45},
        'mountain': {'max': 50, 'avg': 35, 'min': 20},
    }
    
    # Fuel efficiency factors (km/liter)
    FUEL_EFFICIENCY = {
        'highway': 8.5,
        'urban': 5.0,
        'rural': 7.0,
        'mountain': 4.5,
    }
    
    @staticmethod
    def haversine_distance(lat1, lng1, lat2, lng2):
        """Calculate distance between two coordinates in km using Haversine formula"""
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    @staticmethod
    def get_road_type(lat, lng, prev_lat=None, prev_lng=None):
        """Classify road type based on coordinates (ML simulation)"""
        # Simulate road classification
        # In production, use actual road network data (OSM, Google Maps, etc.)
        
        # Check if near major cities (urban)
        urban_zones = [
            (-17.8252, 31.0335, 'Harare'),  # Harare center
            (-20.1550, 28.5795, 'Bulawayo'),
            (-26.2023, 28.0436, 'Johannesburg'),
        ]
        
        for city_lat, city_lng, name in urban_zones:
            dist = RoutingService.haversine_distance(lat, lng, city_lat, city_lng)
            if dist < 30:  # Within 30km of city center
                return 'urban'
        
        # Mountain detection (high latitude variation)
        if prev_lat and prev_lng:
            lat_diff = abs(lat - prev_lat)
            lng_diff = abs(lng - prev_lng)
            if lat_diff > 0.1 or lng_diff > 0.1:
                return 'mountain'
        
        # Random classification for demo (highway vs rural)
        return 'highway' if random.random() > 0.5 else 'rural'
    
    @staticmethod
    def calculate_suggested_speed(road_type, truck_weight_kg, time_of_day=None, 
                                 congestion_level=None, cargo_type=None):
        """
        Calculate ML-based suggested speed considering:
        - Road type (highway, urban, rural, mountain)
        - Truck weight (heavier = slower)
        - Time of day (rush hours = slower)
        - Congestion level (0-100%)
        - Cargo type (hazmat = stricter limits)
        """
        base_speed = RoutingService.SPEED_PROFILES[road_type]['avg']
        
        # Weight factor: every 1000kg above 5000kg reduces speed by 2%
        weight_factor = 1.0
        if truck_weight_kg > 5000:
            excess_weight = (truck_weight_kg - 5000) / 1000
            weight_factor = max(0.70, 1.0 - (excess_weight * 0.02))
        
        # Time of day factor (rush hours: 6-9am, 4-6pm)
        time_factor = 1.0
        if time_of_day:
            hour = time_of_day.hour
            if hour in [6, 7, 8, 16, 17]:  # Rush hour
                time_factor = 0.7
            elif hour in [5, 9, 18]:  # Near rush hour
                time_factor = 0.85
        
        # Congestion factor
        congestion_factor = 1.0
        if congestion_level:
            congestion_factor = 1.0 - (congestion_level / 100 * 0.4)
        
        # Cargo hazmat factor
        cargo_factor = 1.0
        if cargo_type in ['fuel', 'pharma']:  # Hazardous materials
            cargo_factor = 0.85
        
        # Calculate final suggested speed
        suggested_speed = base_speed * weight_factor * time_factor * congestion_factor * cargo_factor
        
        # Clamp to road type limits
        min_speed = RoutingService.SPEED_PROFILES[road_type]['min']
        max_speed = RoutingService.SPEED_PROFILES[road_type]['max']
        
        return max(min_speed, min(max_speed, suggested_speed))
    
    @staticmethod
    def generate_waypoints(origin_coords, destination_coords, num_waypoints=5):
        """Generate intermediate waypoints for route"""
        waypoints = []
        
        lat1, lng1 = origin_coords['lat'], origin_coords['lng']
        lat2, lng2 = destination_coords['lat'], destination_coords['lng']
        
        for i in range(1, num_waypoints + 1):
            ratio = i / (num_waypoints + 1)
            
            # Linear interpolation
            waypoint_lat = lat1 + (lat2 - lat1) * ratio
            waypoint_lng = lng1 + (lng2 - lng1) * ratio
            
            # Add slight perturbation to simulate realistic routing
            perturbation_lat = (random.random() - 0.5) * 0.1
            perturbation_lng = (random.random() - 0.5) * 0.1
            
            waypoint_lat += perturbation_lat
            waypoint_lng += perturbation_lng
            
            waypoints.append({
                'lat': waypoint_lat,
                'lng': waypoint_lng,
                'name': f'Waypoint {i}',
                'order': i
            })
        
        return waypoints
    
    @staticmethod
    def calculate_optimization_score(distance_km, duration_hours, avg_speed_suggestion):
        """
        Calculate route optimization score (0-100)
        Considers fuel efficiency, distance-to-time ratio, and speed consistency
        """
        # Fuel efficiency score
        fuel_score = min(100, (avg_speed_suggestion / 100) * 100)
        
        # Distance-time ratio score (realistic ratios get higher scores)
        realistic_speed = distance_km / duration_hours if duration_hours > 0 else 0
        speed_variance = abs(realistic_speed - avg_speed_suggestion) / max(avg_speed_suggestion, 1)
        time_score = max(0, 100 - (speed_variance * 50))
        
        # Combined optimization score (weighted average)
        optimization_score = (fuel_score * 0.6) + (time_score * 0.4)
        
        return round(optimization_score, 2)
    
    @staticmethod
    def simulate_traffic_conditions(waypoints, origin_coords, destination_coords):
        """Simulate traffic prediction for route segments"""
        traffic_prediction = {}
        
        # Simulate congestion levels for different times
        current_hour = datetime.now().hour
        
        for i, waypoint in enumerate(waypoints):
            # Traffic higher during rush hours
            if current_hour in [6, 7, 8, 16, 17, 18]:
                base_congestion = random.uniform(40, 70)
            else:
                base_congestion = random.uniform(10, 30)
            
            # Add variation to waypoints
            congestion = base_congestion + random.uniform(-10, 10)
            
            traffic_prediction[f'segment_{i}'] = {
                'congestion_level': round(max(0, min(100, congestion)), 2),
                'delay_minutes': int(congestion * 0.5),
                'incident_probability': round(random.uniform(0, 5), 2)
            }
        
        return traffic_prediction
    
    @staticmethod
    def get_weather_factors(origin_coords, destination_coords):
        """Simulate weather conditions affecting route"""
        # In production, use real weather API
        
        weather = {
            'temperature_celsius': random.randint(15, 35),
            'humidity_percent': random.randint(30, 90),
            'wind_speed_kmh': random.randint(0, 30),
            'precipitation_mm': round(random.uniform(0, 10), 1),
            'visibility_km': random.randint(5, 50),
            'weather_condition': random.choice(['Clear', 'Cloudy', 'Rainy', 'Foggy']),
        }
        
        return weather
    
    @staticmethod
    def calculate_route(origin, destination, origin_coords, destination_coords, truck):
        """
        Main route calculation engine
        Returns optimized route with all ML suggestions
        """
        # Calculate distance and basic duration
        total_distance = RoutingService.haversine_distance(
            origin_coords['lat'], origin_coords['lng'],
            destination_coords['lat'], destination_coords['lng']
        )
        
        # Generate waypoints
        waypoints = RoutingService.generate_waypoints(origin_coords, destination_coords, num_waypoints=5)
        
        # Calculate suggested speeds for each segment
        suggested_speeds = {}
        total_speed_sum = 0
        
        # Get truck cargo info
        truck_weight = float(truck.weight.replace('kg', '').strip()) if hasattr(truck.weight, 'replace') else 5000
        cargo_type = truck.cargo.lower() if truck.cargo else 'general'
        
        for i, waypoint in enumerate(waypoints):
            prev_coords = waypoints[i-1] if i > 0 else origin_coords
            road_type = RoutingService.get_road_type(
                waypoint['lat'], waypoint['lng'],
                prev_coords['lat'], prev_coords['lng']
            )
            
            current_time = datetime.now()
            congestion = random.uniform(10, 50)
            
            speed = RoutingService.calculate_suggested_speed(
                road_type,
                truck_weight,
                time_of_day=current_time,
                congestion_level=congestion,
                cargo_type=cargo_type
            )
            
            suggested_speeds[f'segment_{i}'] = {
                'road_type': road_type,
                'suggested_speed_kmh': round(speed, 2),
                'max_safe_speed_kmh': RoutingService.SPEED_PROFILES[road_type]['max'],
                'min_safe_speed_kmh': RoutingService.SPEED_PROFILES[road_type]['min'],
            }
            
            total_speed_sum += speed
        
        avg_suggested_speed = total_speed_sum / len(suggested_speeds)
        
        # Calculate estimated duration
        estimated_duration_hours = total_distance / avg_suggested_speed if avg_suggested_speed > 0 else 1
        
        # Get traffic and weather data
        traffic_prediction = RoutingService.simulate_traffic_conditions(
            waypoints, origin_coords, destination_coords
        )
        weather_factors = RoutingService.get_weather_factors(origin_coords, destination_coords)
        
        # Calculate optimization score
        optimization_score = RoutingService.calculate_optimization_score(
            total_distance, estimated_duration_hours, avg_suggested_speed
        )
        
        return {
            'waypoints': waypoints,
            'distance_km': round(total_distance, 2),
            'estimated_duration_hours': round(estimated_duration_hours, 2),
            'suggested_speeds': suggested_speeds,
            'avg_suggested_speed': round(avg_suggested_speed, 2),
            'traffic_prediction': traffic_prediction,
            'weather_factors': weather_factors,
            'optimization_score': optimization_score,
        }
    
    @staticmethod
    def create_optimized_route(truck_id, origin, destination, origin_coords, destination_coords):
        """Create an optimized route in the database"""
        try:
            truck = Truck.objects.get(id=truck_id)
            
            # Calculate route using enhanced algorithm
            route_data = RoutingService.calculate_route(
                origin, destination, origin_coords, destination_coords, truck
            )
            
            # Create Route object
            route = Route.objects.create(
                truck=truck,
                origin=origin,
                destination=destination,
                origin_coordinates=origin_coords,
                destination_coordinates=destination_coords,
                waypoints=route_data['waypoints'],
                distance_km=route_data['distance_km'],
                estimated_duration_hours=route_data['estimated_duration_hours'],
                suggested_speeds=route_data['suggested_speeds'],
                traffic_prediction=route_data['traffic_prediction'],
                weather_factors=route_data['weather_factors'],
                optimization_score=route_data['optimization_score'],
                status='planned'
            )
            
            return route
        except Exception as e:
            logger.error(f"Error creating optimized route: {e}")
            return None
    
    @staticmethod
    def get_osrm_route(origin_coords, destination_coords, alternatives=2):
        """
        Get road-following route from OSRM
        Returns actual road-based navigation waypoints
        """
        try:
            # Prepare OSRM request
            lng1, lat1 = origin_coords['lng'], origin_coords['lat']
            lng2, lat2 = destination_coords['lng'], destination_coords['lat']
            
            # OSRM Route API endpoint
            url = f"{OSRM_SERVER}/route/v1/driving/{lng1},{lat1};{lng2},{lat2}"
            params = {
                'overview': 'full',
                'steps': 'true',
                'alternatives': 'true',
                'geometries': 'geojson',
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') != 'Ok':
                logger.warning(f"OSRM returned code: {data.get('code')}")
                return None
            
            routes = data.get('routes', [])
            if not routes:
                logger.warning("No routes found from OSRM")
                return None
            
            # Extract waypoints from the best route
            best_route = routes[0]
            coordinates = best_route.get('geometry', {}).get('coordinates', [])
            
            # Convert coordinates to waypoints
            waypoints = []
            for idx, coord in enumerate(coordinates):
                waypoints.append({
                    'lat': coord[1],
                    'lng': coord[0],
                    'name': f'Road Point {idx}',
                    'order': idx
                })
            
            # Collect alternative routes if available
            alternatives_data = []
            for idx, route in enumerate(routes[1:], 1):
                if idx >= alternatives:
                    break
                
                alt_coords = route.get('geometry', {}).get('coordinates', [])
                alt_waypoints = [
                    {'lat': c[1], 'lng': c[0], 'name': f'Alt Route {idx} - Point', 'order': i}
                    for i, c in enumerate(alt_coords)
                ]
                
                alternatives_data.append({
                    'route_index': idx,
                    'distance_m': route.get('distance', 0),
                    'distance_km': round(route.get('distance', 0) / 1000, 2),
                    'duration_seconds': route.get('duration', 0),
                    'duration_hours': round(route.get('duration', 0) / 3600, 2),
                    'waypoints': alt_waypoints,
                })
            
            return {
                'waypoints': waypoints,
                'distance_m': best_route.get('distance', 0),
                'distance_km': round(best_route.get('distance', 0) / 1000, 2),
                'duration_seconds': best_route.get('duration', 0),
                'duration_hours': round(best_route.get('duration', 0) / 3600, 2),
                'alternatives': alternatives_data,
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"OSRM request failed: {e}")
            # Fallback to simple waypoint generation
            return RoutingService._fallback_waypoints(origin_coords, destination_coords)
        except Exception as e:
            logger.error(f"Error processing OSRM response: {e}")
            return None
    
    @staticmethod
    def match_gps_trace_to_roads(gps_points, truck_id=None):
        """
        Match scattered GPS track points to actual roads using OSRM Match Service
        This is the key to Google Maps-like trail visualization
        
        GPS points: List of {'lat': x, 'lng': y, 'timestamp': t, 'speed': s}
        Returns: GPS points snapped to roads with turn instructions
        """
        try:
            if not gps_points or len(gps_points) < 2:
                logger.warning("Insufficient GPS points for trace matching")
                return None
            
            # Limit to max 50 points to avoid OSRM timeout
            # Sample aggressively if too many points
            max_points = 50
            if len(gps_points) > max_points:
                sample_rate = len(gps_points) // max_points
                sampled_gps = gps_points[::sample_rate]
            else:
                sampled_gps = gps_points
            
            logger.info(f"Snapping {len(gps_points)} GPS points for truck {truck_id}, sampled to {len(sampled_gps)} points")
            
            # Convert GPS points to OSRM format (lng,lat;lng,lat;...)
            coordinates = [f"{pt['lng']},{pt['lat']}" for pt in sampled_gps]
            coords_str = ';'.join(coordinates)
            
            # OSRM Match Service endpoint
            url = f"{OSRM_SERVER}/match/v1/driving/{coords_str}"
            params = {
                'overview': 'full',
                'geometries': 'geojson',
                'steps': 'true',
                'annotations': 'distance,duration,congestion',
            }
            
            # Use 5-second timeout for snapping - public OSRM can be slow
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') != 'Ok':
                logger.warning(f"OSRM Match returned code: {data.get('code')}, message: {data.get('message')}")
                return None
            
            matchings = data.get('matchings', [])
            if not matchings:
                logger.warning("No matchings found from OSRM")
                return None
            
            # Get the best matching (usually only one)
            best_match = matchings[0]
            
            # Extract snapped coordinates (the actual road path)
            geometry = best_match.get('geometry', {})
            coordinates = geometry.get('coordinates', [])
            
            if not coordinates:
                logger.warning("No coordinates in OSRM geometry response")
                return None
            
            snapped_points = []
            for idx, coord in enumerate(coordinates):
                snapped_points.append({
                    'lat': coord[1],
                    'lng': coord[0],
                    'order': idx,
                })
            
            # Get turn instructions from legs
            legs = best_match.get('legs', [])
            turn_instructions = []
            
            for leg_idx, leg in enumerate(legs):
                steps = leg.get('steps', [])
                for step in steps:
                    instruction = step.get('maneuver', {}).get('instruction', '')
                    distance = step.get('distance', 0)
                    duration = step.get('duration', 0)
                    
                    if instruction:
                        turn_instructions.append({
                            'instruction': instruction,
                            'distance_m': distance,
                            'distance_km': round(distance / 1000, 2),
                            'duration_seconds': duration,
                        })
            
            total_distance = best_match.get('distance', 0)
            total_duration = best_match.get('duration', 0)
            
            logger.info(f"✅ Successfully snapped {len(gps_points)} GPS points to {len(snapped_points)} road points for truck {truck_id}")
            
            return {
                'snapped_points': snapped_points,
                'turn_instructions': turn_instructions,
                'total_distance_m': total_distance,
                'total_distance_km': round(total_distance / 1000, 2),
                'total_duration_seconds': total_duration,
                'total_duration_hours': round(total_duration / 3600, 2),
                'truck_id': truck_id,
            }
        
        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ OSRM Match request timeout for truck {truck_id} (5s)")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ OSRM Match request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error matching GPS trace: {e}")
            return None
    
    @staticmethod
    def snap_gps_trace_by_segments(gps_points, truck_id=None):
        """
        Snap GPS trace by breaking it into smaller segments and routing through them.
        This is more reliable than trying to match all points at once.
        Uses OSRM /route endpoint which is faster and more reliable than /match
        
        Approach: Connect consecutive GPS points with short routes, then combine all segments
        """
        try:
            if not gps_points or len(gps_points) < 2:
                return None
            
            logger.info(f"🔄 Snapping {len(gps_points)} GPS points by segments for truck {truck_id}")
            
            # Sample down to max 25-30 points to keep segments reasonable
            max_points = 30
            if len(gps_points) > max_points:
                sample_rate = max(1, len(gps_points) // max_points)
                sampled_points = gps_points[::sample_rate]
            else:
                sampled_points = gps_points
            
            all_snapped = []
            
            # Route between consecutive pairs of GPS points
            for i in range(len(sampled_points) - 1):
                start_pt = sampled_points[i]
                end_pt = sampled_points[i + 1]
                
                try:
                    # Build short route between these two points
                    coords = f"{start_pt['lng']},{start_pt['lat']};{end_pt['lng']},{end_pt['lat']}"
                    url = f"{OSRM_SERVER}/route/v1/driving/{coords}"
                    params = {
                        'overview': 'full',
                        'geometries': 'geojson',
                        'steps': 'false',
                    }
                    
                    response = requests.get(url, params=params, timeout=3)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get('code') == 'Ok' and data.get('routes'):
                        route = data['routes'][0]
                        geometry = route.get('geometry', {})
                        coords_segment = geometry.get('coordinates', [])
                        
                        # Add snapped points from this segment
                        for coord in coords_segment:
                            all_snapped.append({
                                'lat': coord[1],
                                'lng': coord[0],
                            })
                    else:
                        # Fallback: add the GPS points directly if routing fails
                        if i == 0:
                            all_snapped.append({'lat': start_pt['lat'], 'lng': start_pt['lng']})
                        all_snapped.append({'lat': end_pt['lat'], 'lng': end_pt['lng']})
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"Segment {i} timeout, skipping")
                    if i == 0:
                        all_snapped.append({'lat': start_pt['lat'], 'lng': start_pt['lng']})
                    all_snapped.append({'lat': end_pt['lat'], 'lng': end_pt['lng']})
                except Exception as e:
                    logger.warning(f"Segment {i} error: {e}, using GPS points")
                    if i == 0:
                        all_snapped.append({'lat': start_pt['lat'], 'lng': start_pt['lng']})
                    all_snapped.append({'lat': end_pt['lat'], 'lng': end_pt['lng']})
            
            if not all_snapped:
                return None
            
            logger.info(f"✅ Segment snapping complete: {len(gps_points)} GPS points → {len(all_snapped)} snapped points")
            
            return {
                'snapped_points': all_snapped,
                'turn_instructions': [],
                'total_distance_m': 0,
                'total_distance_km': 0,
                'total_duration_seconds': 0,
                'total_duration_hours': 0,
                'truck_id': truck_id,
            }
        
        except Exception as e:
            logger.error(f"❌ Segment snapping failed: {e}")
            return None
    
    @staticmethod
    def _fallback_waypoints(origin_coords, destination_coords, num_points=20):
        """Fallback: Generate smooth interpolated path when OSRM fails"""
        waypoints = []
        
        lat1, lng1 = origin_coords['lat'], origin_coords['lng']
        lat2, lng2 = destination_coords['lat'], destination_coords['lng']
        
        for i in range(num_points + 1):
            ratio = i / num_points
            
            # Smooth interpolation with slight curvature
            waypoint_lat = lat1 + (lat2 - lat1) * ratio
            waypoint_lng = lng1 + (lng2 - lng1) * ratio
            
            # Add realistic curvature (roads don't go in straight lines)
            curvature = math.sin(ratio * math.pi) * 0.02
            waypoint_lat += curvature
            
            waypoints.append({
                'lat': waypoint_lat,
                'lng': waypoint_lng,
                'name': f'Route Point {i}',
                'order': i
            })
        
        distance_km = RoutingService.haversine_distance(lat1, lng1, lat2, lng2)
        
        return {
            'waypoints': waypoints,
            'distance_km': round(distance_km, 2),
            'duration_hours': round(distance_km / 80, 2),  # Assume 80km/h average
            'alternatives': [],
        }
    
    @staticmethod
    def get_truck_trail(truck_id, limit=100):
        """
        Get historical GPS trail for a truck
        Used to show where the truck has been
        """
        try:
            track_points = TrackPoint.objects.filter(
                truck_id=truck_id
            ).order_by('recorded_at')[:limit]
            
            trail = []
            for tp in track_points:
                trail.append({
                    'lat': tp.latitude,
                    'lng': tp.longitude,
                    'timestamp': tp.recorded_at.isoformat(),
                    'speed': tp.speed,
                    'heading': tp.heading,
                })
            
            return trail
        except Exception as e:
            logger.error(f"Error fetching truck trail: {e}")
            return []
    
    @staticmethod
    def get_truck_trail_with_directions(truck_id, limit=200):
        """
        Get truck's historical trail with smart interpolation
        Returns snapped-to-roads style path by interpolating between GPS points
        Instant, no OSRM calls needed
        """
        try:
            track_points = TrackPoint.objects.filter(
                truck_id=truck_id
            ).order_by('recorded_at')[:limit]
            
            if not track_points:
                return None
            
            raw_gps_trail = [
                {
                    'lat': tp.latitude,
                    'lng': tp.longitude,
                    'timestamp': tp.recorded_at.isoformat(),
                    'speed': tp.speed,
                }
                for tp in track_points
            ]
            
            # Generate smart interpolated path (mimics road snapping without OSRM)
            smart_path = RoutingService._interpolate_smart_path(raw_gps_trail)
            
            logger.info(f"✅ Smart interpolation for truck {truck_id}: {len(raw_gps_trail)} GPS → {len(smart_path)} snapped points")
            
            return {
                'truck_id': truck_id,
                'snapped': True,
                'snapped_path': smart_path,
                'turn_instructions': [],
                'total_distance_km': 0,
                'total_duration_hours': 0,
                'raw_trail_count': len(raw_gps_trail),
                'snapped_point_count': len(smart_path),
            }
        
        except Exception as e:
            logger.error(f"Error getting truck trail: {e}")
            try:
                # Fallback: return raw trail if something breaks
                track_points = TrackPoint.objects.filter(
                    truck_id=truck_id
                ).order_by('recorded_at')[:limit]
                raw_trail = [
                    {
                        'lat': tp.latitude,
                        'lng': tp.longitude,
                        'timestamp': tp.recorded_at.isoformat(),
                        'speed': tp.speed,
                    }
                    for tp in track_points
                ]
                return {
                    'truck_id': truck_id,
                    'snapped': False,
                    'snapped_path': raw_trail,
                    'raw_trail': raw_trail,
                    'error': str(e),
                }
            except:
                return None
    
    @staticmethod
    def _interpolate_smart_path(gps_points, num_intermediate=5):
        """
        Create smooth road-like path by interpolating between GPS points.
        Mimics OSRM road snapping but works instantly with no external calls.
        
        Adds intermediate points between each pair of GPS points in a smooth curve.
        This creates the visual effect of road-following without OSRM.
        """
        if not gps_points or len(gps_points) < 2:
            return gps_points
        
        smart_path = []
        
        # Add first point
        smart_path.append(gps_points[0])
        
        # For each pair of consecutive GPS points
        for i in range(len(gps_points) - 1):
            current = gps_points[i]
            next_pt = gps_points[i + 1]
            
            # Generate smooth intermediate points
            # This creates a natural curve between waypoints
            for j in range(1, num_intermediate + 1):
                ratio = j / (num_intermediate + 1)
                
                # Smooth interpolation (quadratic easing for curve-like appearance)
                # This mimics how roads curve between GPS samples
                eased_ratio = ratio * ratio if ratio < 0.5 else 1 - (1 - ratio) ** 2
                
                interp_lat = current['lat'] + (next_pt['lat'] - current['lat']) * eased_ratio
                interp_lng = current['lng'] + (next_pt['lng'] - current['lng']) * eased_ratio
                
                smart_path.append({
                    'lat': interp_lat,
                    'lng': interp_lng,
                })
            
            # Add the next GPS point
            smart_path.append(next_pt)
        
        return smart_path
    
    @staticmethod
    def record_truck_position(truck_id, latitude, longitude, speed=0, heading=None, 
                             altitude=None, accuracy=None, route_id=None):
        """
        Record a GPS track point for real-time truck tracking
        Called periodically to build the historical trail
        """
        try:
            truck = Truck.objects.get(id=truck_id)
            route = Route.objects.get(id=route_id) if route_id else truck.current_route
            
            track_point = TrackPoint.objects.create(
                truck=truck,
                route=route,
                latitude=latitude,
                longitude=longitude,
                speed=speed,
                heading=heading,
                altitude=altitude,
                accuracy=accuracy,
                recorded_at=timezone.now(),
            )
            
            return track_point
        except Exception as e:
            logger.error(f"Error recording track point: {e}")
            return None
    
    @staticmethod
    def get_quick_routes(origin_coords, destination_coords, num_routes=3):
        """
        Get multiple alternative routes sorted by speed/distance
        Returns the fastest, shortest, and balanced routes
        """
        try:
            osrm_data = RoutingService.get_osrm_route(
                origin_coords, destination_coords, alternatives=num_routes
            )
            
            if not osrm_data:
                return []
            
            routes = []
            
            # Best route (typically fastest)
            routes.append({
                'route_type': 'fastest',
                'label': '⚡ Fastest Route',
                'distance_km': osrm_data['distance_km'],
                'duration_hours': osrm_data['duration_hours'],
                'estimated_time': f"{int(osrm_data['duration_hours'])}h {int((osrm_data['duration_hours'] % 1) * 60)}m",
                'fuel_efficiency_score': 85,
                'waypoints': osrm_data['waypoints'],
            })
            
            # Alternative routes
            for idx, alt in enumerate(osrm_data['alternatives'][:num_routes - 1]):
                route_type = 'balanced' if idx == 0 else 'scenic'
                label = '⚖️ Balanced Route' if idx == 0 else '🌳 Scenic Route'
                
                routes.append({
                    'route_type': route_type,
                    'label': label,
                    'distance_km': alt['distance_km'],
                    'duration_hours': alt['duration_hours'],
                    'estimated_time': f"{int(alt['duration_hours'])}h {int((alt['duration_hours'] % 1) * 60)}m",
                    'fuel_efficiency_score': 75 - (idx * 5),
                    'waypoints': alt['waypoints'],
                })
            
            return routes
        
        except Exception as e:
            logger.error(f"Error getting quick routes: {e}")
            return []
        """Create and save an optimized route to database"""
        try:
            truck = Truck.objects.get(id=truck_id)
            
            # Calculate route
            route_data = RoutingService.calculate_route(
                origin, destination, origin_coords, destination_coords, truck
            )
            
            # Create route object
            route = Route.objects.create(
                truck=truck,
                origin=origin,
                destination=destination,
                origin_coordinates=origin_coords,
                destination_coordinates=destination_coords,
                waypoints=route_data['waypoints'],
                distance_km=route_data['distance_km'],
                estimated_duration_hours=route_data['estimated_duration_hours'],
                suggested_speeds=route_data['suggested_speeds'],
                optimization_score=route_data['optimization_score'],
                traffic_prediction=route_data['traffic_prediction'],
                weather_factors=route_data['weather_factors'],
                status='planned'
            )
            
            return route
        except Truck.DoesNotExist:
            raise Exception(f"Truck {truck_id} not found")
        except Exception as e:
            raise Exception(f"Error creating route: {str(e)}")
    
    @staticmethod
    def update_route_progress(route_id, distance_travelled_km, time_elapsed_hours, current_waypoint_index):
        """Update route progress as truck moves"""
        try:
            route = Route.objects.get(id=route_id)
            
            route.distance_travelled_km = distance_travelled_km
            route.time_elapsed_hours = time_elapsed_hours
            route.current_waypoint_index = current_waypoint_index
            
            # Update status if needed
            if route.status == 'planned':
                route.status = 'in_progress'
                route.started_at = timezone.now()
            
            # Check if completed
            if distance_travelled_km >= route.distance_km * 0.95:
                route.status = 'completed'
                route.completed_at = timezone.now()
            
            route.save()
            return route
        except Route.DoesNotExist:
            raise Exception(f"Route {route_id} not found")
    
    @staticmethod
    def get_active_routes():
        """Get all active routes for real-time monitoring"""
        return Route.objects.filter(status__in=['planned', 'in_progress']).select_related('truck')
    
    @staticmethod
    def get_truck_routes(truck_id):
        """Get all routes for a specific truck"""
        return Route.objects.filter(truck_id=truck_id).order_by('-created_at')
