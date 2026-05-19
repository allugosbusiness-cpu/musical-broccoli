import urllib.request
import json
import time

print('Waiting for Render deployment...')
time.sleep(60)

mission_data = {
    "mission_number": "TEST-FINAL-FIX",
    "status": "assigned",
    "priority": "high",
    "truck": "d16aaa81-1bba-4a20-b76f-ab8d23ed71f3",
    "driver": "c1c0e021-6f48-42fd-a733-b928784c51bb",
    "origin": {"name": "Main Warehouse"},
    "destination": {"name": "Port Authority"},
    "distance_total_m": 5000
}

try:
    req = urllib.request.Request("https://pulsetrack-back.onrender.com/api/v1/missions/", method="POST")
    req.add_header("Content-Type", "application/json")
    response = urllib.request.urlopen(req, data=json.dumps(mission_data).encode("utf-8"), timeout=10)
    result = json.loads(response.read().decode("utf-8"))
    
    print("HTTP 201 - Mission Created")
    print("Truck: {} (Name: {})".format(result.get("truck"), result.get("truck_name")))
    print("Driver: {} (Name: {})".format(result.get("driver"), result.get("driver_name")))
    print("Status: {}".format(result.get("status")))
    
    if result.get("truck") and result.get("driver"):
        print("\nSUCCESS: Mission properly saved with truck and driver assigned!")
    else:
        print("\nIssue: Truck or driver still not assigned")
except Exception as e:
    print("Error: {}".format(str(e)[:200]))
