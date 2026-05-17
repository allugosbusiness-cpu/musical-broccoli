"""
Fuel Consumption Calculator
Simulates realistic fuel consumption based on driving conditions
"""

import math
from typing import Dict, Tuple


class FuelCalculator:
    """
    Realistic fuel consumption calculation model.
    Based on actual truck fuel efficiency factors.
    """
    
    # Vehicle profiles with base fuel consumption (L/100km)
    VEHICLE_PROFILES = {
        'light_truck': {'base_consumption': 8.0, 'capacity': 60},
        'medium_truck': {'base_consumption': 10.0, 'capacity': 100},
        'heavy_truck': {'base_consumption': 12.0, 'capacity': 150},
        'semi_truck': {'base_consumption': 15.0, 'capacity': 200},
    }
    
    # Terrain elevation change factor (meters per segment)
    # Using elevation gain/loss to calculate terrain difficulty
    ELEVATION_FACTORS = {
        'flat': {'threshold': 10, 'multiplier': 1.0},           # <10m change = flat
        'rolling': {'threshold': 50, 'multiplier': 1.15},       # 10-50m = rolling hills
        'hilly': {'threshold': 100, 'multiplier': 1.35},        # 50-100m = hilly
        'mountainous': {'threshold': 500, 'multiplier': 1.65},  # >100m = mountainous
    }
    
    # Speed efficiency factor (optimal speed ~80-90 km/h)
    # Consumption increases at very low speeds (idling) and very high speeds
    @staticmethod
    def get_speed_factor(speed_kmh: float) -> float:
        """
        Returns fuel consumption multiplier based on speed.
        Optimal around 80-90 km/h for heavy trucks.
        """
        if speed_kmh < 1:  # Idle/stopped
            return 3.0  # High consumption while idling
        elif speed_kmh < 20:
            return 1.8 + (20 - speed_kmh) * 0.04
        elif speed_kmh < 50:
            return 1.3 + (50 - speed_kmh) * 0.01
        elif speed_kmh <= 90:
            # Optimal range - linear interpolation
            return 0.9 + (speed_kmh - 90) * 0.001
        elif speed_kmh <= 120:
            # Over-speed penalty
            return 1.0 + (speed_kmh - 90) * 0.02
        else:
            # Highway overspeed
            return 1.6 + (speed_kmh - 120) * 0.05
    
    @staticmethod
    def get_load_factor(load_percent: float, fuel_in_tank: float = 100) -> float:
        """
        Load impact on fuel consumption.
        Every 10% load increase = ~2-3% fuel increase.
        """
        if load_percent < 20:
            return 1.0
        elif load_percent < 50:
            return 1.0 + (load_percent - 20) * 0.025
        elif load_percent < 80:
            return 1.75 + (load_percent - 50) * 0.035
        else:
            return 2.7 + (load_percent - 80) * 0.04
    
    @staticmethod
    def get_terrain_factor(elevation_gain_m: float) -> float:
        """
        Terrain difficulty based on elevation change.
        Applies to the segment being traveled.
        """
        abs_elevation = abs(elevation_gain_m)
        
        if abs_elevation < 10:
            return 1.0
        elif abs_elevation < 50:
            return 1.15
        elif abs_elevation < 100:
            return 1.35
        elif abs_elevation < 300:
            return 1.65
        else:
            return 2.0
    
    @staticmethod
    def get_weather_factor(weather_conditions: Dict) -> float:
        """
        Weather impact on fuel consumption.
        Default factor: 1.0 (no impact)
        """
        factor = 1.0
        
        if weather_conditions.get('rain', False):
            factor += 0.08  # 8% increase in wet conditions
        
        if weather_conditions.get('fog', False):
            factor += 0.05  # 5% increase in fog (lower visibility, cautious driving)
        
        if weather_conditions.get('wind_speed', 0) > 30:
            factor += (weather_conditions['wind_speed'] - 30) * 0.005  # Headwind penalty
        
        if weather_conditions.get('temperature', 20) < 0:
            # Cold weather increases consumption
            factor += (0 - weather_conditions['temperature']) * 0.01
        
        return factor
    
    @staticmethod
    def calculate_segment_consumption(
        distance_km: float,
        avg_speed_kmh: float,
        elevation_gain_m: float,
        load_percent: float,
        vehicle_type: str = 'medium_truck',
        weather: Dict = None,
        time_stopped_minutes: float = 0,
    ) -> float:
        """
        Calculate fuel consumption for a route segment.
        
        Args:
            distance_km: Distance of segment
            avg_speed_kmh: Average speed during segment
            elevation_gain_m: Net elevation change
            load_percent: Cargo load percentage (0-100)
            vehicle_type: Type of vehicle
            weather: Weather conditions dict
            time_stopped_minutes: Time spent idle/stopped
        
        Returns:
            Fuel consumed in liters
        """
        if weather is None:
            weather = {}
        
        if vehicle_type not in FuelCalculator.VEHICLE_PROFILES:
            vehicle_type = 'medium_truck'
        
        base_consumption = FuelCalculator.VEHICLE_PROFILES[vehicle_type]['base_consumption']
        
        # Calculate consumption for moving distance
        speed_factor = FuelCalculator.get_speed_factor(avg_speed_kmh)
        load_factor = FuelCalculator.get_load_factor(load_percent)
        terrain_factor = FuelCalculator.get_terrain_factor(elevation_gain_m)
        weather_factor = FuelCalculator.get_weather_factor(weather)
        
        movement_consumption = (
            distance_km *
            (base_consumption / 100) *
            speed_factor *
            load_factor *
            terrain_factor *
            weather_factor
        )
        
        # Add idle consumption
        idle_consumption = (time_stopped_minutes / 60) * (base_consumption / 6)  # ~2L/hour idle
        
        return movement_consumption + idle_consumption
    
    @staticmethod
    def calculate_trip_consumption(
        distance_km: float,
        duration_minutes: float,
        avg_speed_kmh: float,
        total_elevation_gain_m: float,
        load_percent: float,
        vehicle_type: str = 'medium_truck',
        weather: Dict = None,
        stops_count: int = 0,
        stop_duration_minutes: float = 10,
    ) -> Dict:
        """
        Calculate total fuel consumption for a complete trip.
        
        Returns:
            {
                'total_consumption_liters': float,
                'distance_consumption': float,
                'idle_consumption': float,
                'efficiency_kmpl': float,
                'estimated_range_km': float,
                'breakdown': {
                    'speed_factor': float,
                    'load_factor': float,
                    'terrain_factor': float,
                    'weather_factor': float,
                }
            }
        """
        if weather is None:
            weather = {}
        
        if vehicle_type not in FuelCalculator.VEHICLE_PROFILES:
            vehicle_type = 'medium_truck'
        
        base_consumption = FuelCalculator.VEHICLE_PROFILES[vehicle_type]['base_consumption']
        tank_capacity = FuelCalculator.VEHICLE_PROFILES[vehicle_type]['capacity']
        
        # Calculate all factors
        speed_factor = FuelCalculator.get_speed_factor(avg_speed_kmh)
        load_factor = FuelCalculator.get_load_factor(load_percent)
        terrain_factor = FuelCalculator.get_terrain_factor(total_elevation_gain_m)
        weather_factor = FuelCalculator.get_weather_factor(weather)
        
        # Distance-based consumption
        distance_consumption = (
            distance_km *
            (base_consumption / 100) *
            speed_factor *
            load_factor *
            terrain_factor *
            weather_factor
        )
        
        # Idle consumption (stops and traffic)
        total_idle_minutes = (stops_count * stop_duration_minutes) + (
            (duration_minutes - (distance_km / max(avg_speed_kmh, 1) * 60)) if avg_speed_kmh > 0 else duration_minutes
        )
        idle_consumption = (total_idle_minutes / 60) * (base_consumption / 6)
        
        total_consumption = distance_consumption + idle_consumption
        efficiency = distance_km / total_consumption if total_consumption > 0 else 0
        
        # Estimate range with full tank
        estimated_range = (tank_capacity * efficiency) if efficiency > 0 else 0
        
        return {
            'total_consumption_liters': round(total_consumption, 2),
            'distance_consumption': round(distance_consumption, 2),
            'idle_consumption': round(idle_consumption, 2),
            'efficiency_kmpl': round(efficiency, 2),
            'estimated_range_km': round(estimated_range, 2),
            'tank_capacity_liters': tank_capacity,
            'breakdown': {
                'speed_factor': round(speed_factor, 3),
                'load_factor': round(load_factor, 3),
                'terrain_factor': round(terrain_factor, 3),
                'weather_factor': round(weather_factor, 3),
            }
        }
    
    @staticmethod
    def estimate_fuel_remaining(
        initial_fuel_liters: float,
        consumption_rate_lph: float,
        elapsed_hours: float,
    ) -> float:
        """
        Estimate remaining fuel after elapsed time.
        
        Args:
            initial_fuel_liters: Starting fuel
            consumption_rate_lph: Consumption rate in liters per hour
            elapsed_hours: Time elapsed
        
        Returns:
            Remaining fuel in liters
        """
        consumed = consumption_rate_lph * elapsed_hours
        return max(0, initial_fuel_liters - consumed)
    
    @staticmethod
    def calculate_mph_to_kmpl(efficiency_kmpl: float) -> float:
        """Convert kilometers per liter to miles per gallon."""
        return efficiency_kmpl * 2.352
