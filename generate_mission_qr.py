#!/usr/bin/env python
"""
Generate test mission QR codes for mobile app testing
Run this script to create sample missions and generate their QR codes
"""

import os
import sys
import django
import json
import qrcode
from io import BytesIO
import base64
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
sys.path.insert(0, '/path/to/fleet/management/server')
django.setup()

from api.models_v2 import FleetDriver, FleetTruck, FleetMission, MissionStatus

def generate_mission_qr_codes():
    """Generate QR codes for all available missions"""
    
    # Get all missions that are not completed
    missions = FleetMission.objects.filter(
        status__in=['pending', 'assigned', 'in_progress']
    )
    
    if not missions.exists():
        print("No missions found. Creating a test mission first...")
        
        # Get first available driver and truck
        driver = FleetDriver.objects.first()
        truck = FleetTruck.objects.first()
        
        if not driver or not truck:
            print("ERROR: No drivers or trucks found. Please create them first.")
            return
        
        # Create test mission
        mission = FleetMission.objects.create(
            mission_number='TEST-001',
            driver=driver,
            truck=truck,
            status='assigned',
            origin_latitude=40.7128,
            origin_longitude=-74.0060,
            destination_latitude=40.7589,
            destination_longitude=-73.9851,
            destination_address='Times Square, New York, NY',
        )
        print(f"Created test mission: {mission.id}")
        missions = [mission]
    
    print(f"\nGenerating QR codes for {missions.count()} missions...\n")
    
    for mission in missions:
        if not mission.driver or not mission.truck:
            print(f"⚠️  Mission {mission.mission_number} - Missing driver or truck, skipping")
            continue
        
        # Create QR code data
        qr_data = {
            'type': 'driver_mission_assignment',
            'mission_id': str(mission.id),
            'driver_id': str(mission.driver.id),
            'truck_id': str(mission.truck.id),
            'driver_name': mission.driver.name,
            'driver_phone': mission.driver.phone_number,
            'destination_latitude': float(mission.destination_latitude),
            'destination_longitude': float(mission.destination_longitude),
            'origin_latitude': float(mission.origin_latitude),
            'origin_longitude': float(mission.origin_longitude),
            'mission_number': mission.mission_number,
            'destination_address': mission.destination_address or '',
            'timestamp': datetime.now().isoformat(),
        }
        
        qr_json = json.dumps(qr_data)
        
        # Generate QR code image
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_json)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color='black', back_color='white')
        
        # Save as file
        filename = f"mission_{mission.mission_number}.png"
        img.save(filename)
        
        # Also create base64 version
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Save base64 to text file for easy sharing
        base64_filename = f"mission_{mission.mission_number}_base64.txt"
        with open(base64_filename, 'w') as f:
            f.write(f"Mission QR Code (Base64):\n")
            f.write(f"data:image/png;base64,{img_base64}\n\n")
            f.write(f"Mission Data (for testing):\n")
            f.write(json.dumps(qr_data, indent=2))
        
        print(f"✅ Mission: {mission.mission_number}")
        print(f"   Driver: {mission.driver.name} ({mission.driver.phone_number})")
        print(f"   Truck: {mission.truck.truck_name}")
        print(f"   QR Code saved: {filename}")
        print(f"   Data saved: {base64_filename}")
        print(f"   Destination: {qr_data['destination_latitude']}, {qr_data['destination_longitude']}")
        print()

if __name__ == '__main__':
    print("=" * 60)
    print("FLEET MANAGEMENT - MISSION QR CODE GENERATOR")
    print("=" * 60)
    generate_mission_qr_codes()
    print("Done!")
