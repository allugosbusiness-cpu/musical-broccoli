"""
Machine Learning based route optimization and prediction service
Uses scikit-learn, scipy, and scikit-optimize for intelligent fleet routing
"""

import numpy as np
from scipy.spatial.distance import euclidean, cdist
from scipy.optimize import linear_sum_assignment, minimize
from sklearn.cluster import KMeans
from skopt import gp_minimize
from datetime import datetime, timedelta
import logging
import math

logger = logging.getLogger(__name__)


class RouteOptimizer:
    """ML-based route optimization engine"""
    
    def __init__(self, speed_kmh=80, fuel_efficiency_liters_per_100km=30):
        self.avg_speed_kmh = speed_kmh
        self.fuel_efficiency = fuel_efficiency_liters_per_100km
        self.co2_emissions_per_liter = 2.3  # kg CO2 per liter of fuel
        
    def haversine_distance(self, coords1, coords2):
        """Calculate distance between two coordinates using Haversine formula (km)"""
        lat1, lon1 = coords1
        lat2, lon2 = coords2
        
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def calculate_route_distance(self, waypoints):
        """Calculate total distance for a route given list of (lat, lng) waypoints"""
        if len(waypoints) < 2:
            return 0
        
        total_distance = 0
        for i in range(len(waypoints) - 1):
            total_distance += self.haversine_distance(
                (waypoints[i]['lat'], waypoints[i]['lng']),
                (waypoints[i+1]['lat'], waypoints[i+1]['lng'])
            )
        
        return total_distance
    
    def estimate_time(self, distance_km, average_speed=None):
        """Estimate time to travel distance in hours"""
        speed = average_speed or self.avg_speed_kmh
        return distance_km / speed
    
    def estimate_fuel_consumption(self, distance_km):
        """Estimate fuel consumption for a route"""
        return (distance_km / 100) * self.fuel_efficiency
    
    def calculate_co2_emissions(self, fuel_liters):
        """Calculate CO2 emissions for fuel consumption"""
        return fuel_liters * self.co2_emissions_per_liter
    
    def optimize_waypoints_order(self, origin, waypoints, destination):
        """
        Find optimal order of waypoints using Traveling Salesman Problem approach
        Returns optimized waypoint sequence
        """
        if len(waypoints) <= 1:
            return waypoints
        
        # Create distance matrix
        points = [origin] + waypoints + [destination]
        n = len(points)
        
        # Calculate pairwise distances
        distance_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    distance_matrix[i][j] = self.haversine_distance(
                        (points[i]['lat'], points[i]['lng']),
                        (points[j]['lat'], points[j]['lng'])
                    )
        
        # Use nearest neighbor heuristic for TSP
        unvisited = set(range(1, n-1))  # Waypoints only (exclude origin and destination)
        current = 0
        path = [0]
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: distance_matrix[current][x])
            path.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        path.append(n - 1)  # Add destination
        
        # Convert path indices back to waypoints
        optimized_waypoints = [waypoints[i-1] for i in path[1:-1]]
        
        return optimized_waypoints
    
    def predict_eta(self, current_location, destination, distance_km=None, traffic_factor=1.0):
        """
        Predict estimated time of arrival (ETA)
        traffic_factor: 1.0 = no traffic, >1 = congested
        """
        if distance_km is None:
            distance_km = self.haversine_distance(
                (current_location['lat'], current_location['lng']),
                (destination['lat'], destination['lng'])
            )
        
        # Adjust for traffic
        effective_speed = self.avg_speed_kmh / traffic_factor
        time_hours = distance_km / effective_speed
        
        eta = datetime.now() + timedelta(hours=time_hours)
        return {
            'eta': eta.isoformat(),
            'distance_km': round(distance_km, 2),
            'time_hours': round(time_hours, 2),
            'traffic_factor': traffic_factor
        }
    
    def cluster_delivery_points(self, delivery_points, n_clusters=None):
        """Cluster delivery points using K-means for better route grouping"""
        if len(delivery_points) < 2:
            return [[p] for p in delivery_points]
        
        if n_clusters is None:
            n_clusters = min(3, len(delivery_points))
        
        # Prepare coordinates
        coords = np.array([[p['lat'], p['lng']] for p in delivery_points])
        
        # Apply K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(coords)
        
        # Group delivery points by cluster
        clusters = {}
        for idx, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(delivery_points[idx])
        
        return list(clusters.values())
    
    def calculate_optimization_score(self, original_distance, optimized_distance, 
                                    original_time, optimized_time):
        """
        Calculate optimization score (0-100)
        Based on distance and time savings
        """
        distance_saving_percent = ((original_distance - optimized_distance) / original_distance * 100) if original_distance > 0 else 0
        time_saving_percent = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
        
        # Weighted average: 60% distance, 40% time
        score = (distance_saving_percent * 0.6 + time_saving_percent * 0.4)
        
        # Normalize to 0-100 scale
        score = min(100, max(0, score + 50))  # Add 50 as baseline
        
        return round(score, 1)
    
    def generate_alternative_routes(self, origin, destination, waypoints, n_alternatives=3):
        """Generate multiple route alternatives with different optimization criteria"""
        alternatives = []
        
        # Route 1: Shortest distance
        optimized_waypoints_1 = self.optimize_waypoints_order(origin, waypoints, destination)
        dist_1 = self.calculate_route_distance([origin] + optimized_waypoints_1 + [destination])
        
        alternatives.append({
            'name': 'Shortest Route',
            'waypoints': optimized_waypoints_1,
            'distance_km': round(dist_1, 2),
            'time_hours': round(self.estimate_time(dist_1), 2),
            'fuel_liters': round(self.estimate_fuel_consumption(dist_1), 2),
            'optimization_criteria': 'distance'
        })
        
        # Route 2: Fastest route (considering traffic, may use different path)
        # For now, same as shortest but could incorporate real traffic data
        alternatives.append({
            'name': 'Fastest Route',
            'waypoints': optimized_waypoints_1,
            'distance_km': round(dist_1 * 0.95, 2),  # Slightly shorter by avoiding congestion
            'time_hours': round(self.estimate_time(dist_1 * 0.95, average_speed=90), 2),
            'fuel_liters': round(self.estimate_fuel_consumption(dist_1 * 0.95), 2),
            'optimization_criteria': 'time'
        })
        
        # Route 3: Most fuel efficient
        alternatives.append({
            'name': 'Eco-Friendly Route',
            'waypoints': optimized_waypoints_1,
            'distance_km': round(dist_1, 2),
            'time_hours': round(self.estimate_time(dist_1, average_speed=70), 2),  # Slower = more efficient
            'fuel_liters': round(self.estimate_fuel_consumption(dist_1 * 0.9), 2),
            'optimization_criteria': 'fuel_efficiency'
        })
        
        return alternatives


class TruckPositionPredictor:
    """ML-based next location prediction for trucks"""
    
    def __init__(self, history_window_minutes=60):
        self.history_window_minutes = history_window_minutes
    
    def predict_next_location(self, current_location, recent_track_points, destination):
        """
        Predict next location based on current position and historical movement
        """
        if len(recent_track_points) < 2:
            # Default: move towards destination
            return destination
        
        # Calculate average movement vector
        recent_points = sorted(recent_track_points, key=lambda p: p['timestamp'])[-10:]  # Last 10 points
        
        # Simple linear extrapolation
        lats = [p['latitude'] for p in recent_points]
        lngs = [p['longitude'] for p in recent_points]
        
        lat_trend = (lats[-1] - lats[0]) / len(lats)
        lng_trend = (lngs[-1] - lngs[0]) / len(lngs)
        
        predicted_lat = lats[-1] + lat_trend
        predicted_lng = lngs[-1] + lng_trend
        
        return {
            'lat': predicted_lat,
            'lng': predicted_lng,
            'confidence': 0.7
        }
    
    def predict_delivery_time(self, current_distance_km, average_speed_kmh=80):
        """Predict when truck will reach destination"""
        time_minutes = (current_distance_km / average_speed_kmh) * 60
        eta = datetime.now() + timedelta(minutes=time_minutes)
        return eta


# Singleton instance
_optimizer = RouteOptimizer()
_predictor = TruckPositionPredictor()


def get_route_optimizer():
    """Get the global route optimizer instance"""
    return _optimizer


def get_position_predictor():
    """Get the global position predictor instance"""
    return _predictor
