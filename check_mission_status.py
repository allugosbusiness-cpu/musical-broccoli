import urllib.request, json

print("1. Checking all missions in the system...")
try:
    req = urllib.request.Request("https://pulsetrack-back.onrender.com/api/v1/missions/", method="GET")
    req.add_header("Accept", "application/json")
    response = urllib.request.urlopen(req, timeout=10)
    data = json.loads(response.read().decode("utf-8"))
    
    if isinstance(data, dict) and "results" in data:
        missions = data["results"]
    else:
        missions = data if isinstance(data, list) else []
    
    print(f"  Total missions: {len(missions)}")
    for m in missions[-5:]:  # Show last 5
        print(f"    - ID: {m.get('id')}, Number: {m.get('mission_number')}, Status: {m.get('status')}, Driver: {m.get('driver_id')}")
except Exception as e:
    print(f"  Error: {e}")

print("\n2. Checking driver details...")
try:
    req = urllib.request.Request("https://pulsetrack-back.onrender.com/api/v1/drivers/2ab69512-033c-4bf1-b5cb-0d6b28472af1/", method="GET")
    req.add_header("Accept", "application/json")
    response = urllib.request.urlopen(req, timeout=10)
    data = json.loads(response.read().decode("utf-8"))
    print(f"  Driver: {data.get('name')}")
    print(f"  Truck ID: {data.get('truck_id')}")
    print(f"  Status: {data.get('status')}")
except Exception as e:
    print(f"  Error: {e}")
