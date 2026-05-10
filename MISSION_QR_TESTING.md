# Mission QR Code Testing Guide

## Overview
This guide explains how to generate and test mission QR codes for the PulseTrack mobile app.

## Quick Start: Generate Test Missions

### Using the Backend Endpoint (Recommended)

If you already have missions in the database, you can generate QR codes via the API:

```bash
# Get QR code for a specific mission
curl http://localhost:8000/api/v1/mobile/mission/{MISSION_ID}/generate-qr/
```

**Response:**
```json
{
  "mission_id": "abc123",
  "driver_id": "driver-id",
  "truck_id": "truck-id",
  "qr_code_data": "{...json...}",
  "qr_code_image": "data:image/png;base64,..."
}
```

### Using the Python Generator Script

For quick testing without backend setup:

```bash
cd server
python manage.py shell < generate_mission_qr.py
```

Or run it directly:
```bash
python generate_mission_qr.py
```

This will:
1. Find all unassigned missions in the database
2. Assign them to available drivers
3. Generate PNG files: `mission_TEST-001.png`
4. Create text files with base64-encoded QR codes for easy sharing

**Output Files:**
- `mission_TEST-001.png` - Scannable QR code image
- `mission_TEST-001_base64.txt` - Base64 data and mission JSON

## Testing in the Mobile App

### Method 1: Using the QR Debugger Tool

The app includes a **QR Code Debugger** for testing without scanning:

1. Open the app on your device (Expo Go)
2. Click **"🔍 QR Code Debugger"** button on phone entry screen
3. Copy mission QR data from the Python generator
4. Paste it into the debug screen
5. Click **"Parse QR Code"**
6. Verify the data structure matches expected format

### Method 2: Scanning Physical QR Codes

1. Generate PNG QR codes using the Python script
2. Display QR code on another device/paper
3. On mobile app, tap **"📱 Scan Mission QR Code"** after registration
4. Point camera at QR code
5. Mission should start tracking

### Method 3: Scanning from Printed QR Codes

1. Run the Python generator to create PNG files
2. Print the PNG images
3. Scan them with the phone camera

## Expected QR Code Format

### Mission QR Code (driver_mission_assignment)

```json
{
  "type": "driver_mission_assignment",
  "mission_id": "550e8400-e29b-41d4-a716-446655440000",
  "driver_id": "d1a2b3c4-e5f6-41d4-a716-446655440001",
  "truck_id": "t1a2b3c4-e5f6-41d4-a716-446655440002",
  "driver_name": "John Doe",
  "driver_phone": "1234567890",
  "destination_latitude": 40.7589,
  "destination_longitude": -73.9851,
  "origin_latitude": 40.7128,
  "origin_longitude": -74.0060,
  "mission_number": "MISSION-001",
  "destination_address": "Times Square, New York",
  "timestamp": "2026-05-08T12:00:00.000Z"
}
```

### Truck Registration QR Code (truck_registration)

```json
{
  "truck_id": "t1a2b3c4-e5f6-41d4-a716-446655440002",
  "truck_name": "Truck 001",
  "backend_url": "http://192.168.1.100:8000/api/v1",
  "timestamp": "2026-05-08T12:00:00.000Z"
}
```

## Troubleshooting

### "QR code format not recognized"

**Solution:** Ensure your QR code contains the correct JSON structure. Use the QR Debugger tool to test.

**Check:**
- Does it have `type: "driver_mission_assignment"` for missions?
- Does it have all required fields?
- Is it valid JSON?

### "Mission not found"

**Solution:** Verify the mission_id exists in your backend database.

```bash
# Check missions in database
python manage.py shell
>>> from api.models_v2 import FleetMission
>>> missions = FleetMission.objects.all()
>>> for m in missions:
...     print(f"{m.id}: {m.mission_number}")
```

### "Driver does not match mission"

**Solution:** The driver_id in the QR code must match the currently logged-in driver.

Make sure you registered with the same phone number that's assigned to the driver in the mission.

## Creating Test Data

### Create Test Driver & Truck

```bash
python manage.py shell
```

```python
from api.models_v2 import FleetDriver, FleetTruck, FleetMission

# Create truck
truck = FleetTruck.objects.create(
    truck_name="Test Truck",
    license_plate="TEST123"
)

# Create driver
driver = FleetDriver.objects.create(
    name="Test Driver",
    phone_number="5551234567",
    truck=truck
)

# Create mission
mission = FleetMission.objects.create(
    mission_number="TEST-001",
    driver=driver,
    truck=truck,
    status="assigned",
    origin_latitude=40.7128,
    origin_longitude=-74.0060,
    destination_latitude=40.7589,
    destination_longitude=-73.9851,
    destination_address="Test Destination"
)

# Generate QR code
import json
from rest_framework.authtoken.models import Token

qr_data = {
    "type": "driver_mission_assignment",
    "mission_id": str(mission.id),
    "driver_id": str(driver.id),
    "truck_id": str(truck.id),
    "driver_name": driver.name,
    "driver_phone": driver.phone_number,
    "destination_latitude": float(mission.destination_latitude),
    "destination_longitude": float(mission.destination_longitude),
    "origin_latitude": float(mission.origin_latitude),
    "origin_longitude": float(mission.origin_longitude),
    "mission_number": mission.mission_number,
    "destination_address": mission.destination_address
}

print(json.dumps(qr_data))
```

## API Endpoints

### Generate Mission QR Code
```
GET /api/v1/mobile/mission/{mission_id}/generate-qr/
```

**Response (200 OK):**
```json
{
  "mission_id": "...",
  "driver_id": "...",
  "truck_id": "...",
  "qr_code_data": "{...}",
  "qr_code_image": "data:image/png;base64,..."
}
```

### Generate Truck QR Code
```
GET /api/v1/mobile/truck/{truck_id}/generate-qr/
```

**Response (200 OK):**
```json
{
  "truck_id": "...",
  "qr_code_data": "{...}",
  "qr_code_image": "data:image/png;base64,..."
}
```

## Next Steps

1. ✅ Generate test missions using Python script
2. ✅ Test QR parsing with debugger tool
3. ✅ Register as test driver
4. ✅ Scan mission QR to start tracking
5. ✅ Monitor location updates in dashboard
6. ✅ Confirm delivery upon arrival

---

**Need Help?**
- Check the QR Debugger tool for data validation
- Review mission details in the backend admin
- Check mobile app logs for errors
