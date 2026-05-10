#!/usr/bin/env python
"""
Generate sample GPS trail data for testing the truck tracking system
Creates a realistic path from Harare to Mutare with multiple trackpoints
"""
import requests
import time
import json
from datetime import datetime, timedelta

# Backend API URL
API_BASE = "http://localhost:8000/api"

# Route: Harare to Mutare (approximately 256 km northeast)
# Harare: -17.8252, 31.0335
# Mutare: -18.9674, 32.6652

# Generate GPS waypoints along the route
def generate_route_waypoints(start_lat, start_lng, end_lat, end_lng, num_points=30):
    """Generate intermediate GPS points between start and end coordinates"""
    waypoints = []
    for i in range(num_points):
        ratio = i / num_points
        lat = start_lat + (end_lat - start_lat) * ratio
        lng = start_lng + (end_lng - start_lng) * ratio
        
        # Add small random variations to make it look realistic
        import random
        lat += random.uniform(-0.01, 0.01)
        lng += random.uniform(-0.01, 0.01)
        
        waypoints.append({'lat': lat, 'lng': lng})
    
    return waypoints

def record_truck_position(truck_id, latitude, longitude, speed=60, heading=45):
    """Record a single GPS track point for a truck"""
    payload = {
        'latitude': latitude,
        'longitude': longitude,
        'speed': speed,
        'heading': heading,
        'altitude': 1500,
        'accuracy': 10
    }
    
    url = f"{API_BASE}/trucks/{truck_id}/record_position/"
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201:
            print(f"✓ Recorded position for {truck_id}: ({latitude:.4f}, {longitude:.4f}) at {speed} km/h")
            return True
        else:
            print(f"✗ Failed to record position: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error recording position: {e}")
        return False

def generate_trail_for_truck(truck_id, start_lat, start_lng, end_lat, end_lng, num_points=30):
    """Generate and record a complete GPS trail for a truck"""
    print(f"\n🚚 Generating GPS trail for {truck_id}...")
    print(f"   From ({start_lat:.4f}, {start_lng:.4f}) to ({end_lat:.4f}, {end_lng:.4f})")
    
    waypoints = generate_route_waypoints(start_lat, start_lng, end_lat, end_lng, num_points)
    
    success_count = 0
    for i, wp in enumerate(waypoints):
        # Vary speed realistically (highways faster, cities slower)
        speed = 80 + (i % 10 - 5)  # 75-85 km/h
        
        if record_truck_position(truck_id, wp['lat'], wp['lng'], speed=speed, heading=45):
            success_count += 1
            time.sleep(0.1)  # Small delay between requests
    
    print(f"   ✓ Generated {success_count}/{num_points} track points")
    return success_count

def main():
    print("=" * 60)
    print("FLEET MANAGEMENT - GPS TRAIL DATA GENERATOR")
    print("=" * 60)
    
    # Define routes for different trucks
    routes = [
        {
            'truck_id': 'TRUCK-001',
            'start': {'lat': -17.8252, 'lng': 31.0335},  # Harare
            'end': {'lat': -18.9674, 'lng': 32.6652},    # Mutare
            'points': 25
        },
        {
            'truck_id': 'TRUCK-002',
            'start': {'lat': -20.1550, 'lng': 28.5795},  # Bulawayo
            'end': {'lat': -17.8252, 'lng': 31.0335},    # Harare
            'points': 25
        },
        {
            'truck_id': 'TRUCK-003',
            'start': {'lat': -17.8252, 'lng': 31.0335},  # Harare
            'end': {'lat': -19.0160, 'lng': 29.1543},    # Chitungwiza area
            'points': 15
        },
        {
            'truck_id': 'TRUCK-004',
            'start': {'lat': -20.1550, 'lng': 28.5795},  # Bulawayo
            'end': {'lat': -19.5, 'lng': 29.5},          # Somewhere in middle
            'points': 20
        },
        {
            'truck_id': 'TRUCK-005',
            'start': {'lat': -17.8252, 'lng': 31.0335},  # Harare
            'end': {'lat': -18.5, 'lng': 31.8},          # Northeast of Harare
            'points': 15
        },
    ]
    
    total_generated = 0
    
    for route in routes:
        count = generate_trail_for_truck(
            route['truck_id'],
            route['start']['lat'],
            route['start']['lng'],
            route['end']['lat'],
            route['end']['lng'],
            route['points']
        )
        total_generated += count
    
    print("\n" + "=" * 60)
    print(f"✓ COMPLETE: Generated {total_generated} total track points")
    print("=" * 60)
    
    print("\n🗺️  Testing the truck_trail_with_directions endpoint...")
    time.sleep(1)
    
    for route in routes:
        truck_id = route['truck_id']
        url = f"{API_BASE}/trucks/{truck_id}/truck_trail_with_directions/?limit=100"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ {truck_id}:")
                print(f"  - Snapped: {data.get('snapped', False)}")
                print(f"  - Trail points: {data.get('raw_trail_count', 0)}")
                if data.get('snapped_path'):
                    print(f"  - Snapped waypoints: {len(data.get('snapped_path', []))}")
                if data.get('turn_instructions'):
                    print(f"  - Turn instructions: {len(data.get('turn_instructions', []))}")
                print(f"  - Distance: {data.get('total_distance_km', 0):.1f} km")
                print(f"  - Duration: {data.get('total_duration_hours', 0):.2f} hours")
            else:
                print(f"\n✗ {truck_id}: HTTP {response.status_code}")
        except Exception as e:
            print(f"\n✗ {truck_id}: Error - {e}")

if __name__ == '__main__':
    main()
