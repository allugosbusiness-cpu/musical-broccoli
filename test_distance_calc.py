import urllib.request, json, time

print("Waiting for Render deployment...")
time.sleep(90)

print("Testing mission creation with distance calculation...")

mission_data = {
    "mission_number": "DISTANCE-TEST-001",
    "status": "planned",
    "priority": "high",
    "truck": "d16aaa81-1bba-4a20-b76f-ab8d23ed71f3",
    "driver": "c1c0e021-6f48-42fd-a733-b928784c51bb",
    "origin": {"name": "Main Warehouse", "lat": -1.2921, "lng": 36.8219},
    "destination": {"name": "Port Authority", "lat": -1.2850, "lng": 36.8270}
}

try:
    req = urllib.request.Request("https://pulsetrack-back.onrender.com/api/v1/missions/", method="POST")
    req.add_header("Content-Type", "application/json")
    response = urllib.request.urlopen(req, data=json.dumps(mission_data).encode('utf-8'), timeout=10)
    result = json.loads(response.read().decode("utf-8"))
    
    print(f"✓ HTTP 201 - Mission Created")
    print(f"  Mission #: {result.get('mission_number')}")
    print(f"  Truck Name: {result.get('truck_name')}")
    print(f"  Driver Name: {result.get('driver_name')}")
    print(f"  Status: {result.get('status')}")
    distance_m = result.get('distance_total_m', 0)
    distance_km = float(distance_m) / 1000 if distance_m else 0
    print(f"  Distance: {distance_m} meters = {distance_km:.2f} km")
    
    success = result.get('truck_name') and result.get('driver_name') and result.get('distance_total_m')
    if success:
        print(f"\n✓✓✓ SUCCESS: All fields properly set (truck, driver, distance)!")
    else:
        print(f"\n⚠ Check: truck_name={result.get('truck_name')}, driver_name={result.get('driver_name')}, distance={result.get('distance_total_m')}")
except Exception as e:
    print(f"✗ Error: {str(e)[:300]}")
