import urllib.request, json

print("1. Getting all trucks...")
try:
    req = urllib.request.Request("https://pulsetrack-back.onrender.com/api/v1/trucks/", method="GET")
    req.add_header("Accept", "application/json")
    response = urllib.request.urlopen(req, timeout=10)
    data = json.loads(response.read().decode("utf-8"))
    
    if isinstance(data, dict) and "results" in data:
        trucks = data["results"]
    else:
        trucks = data if isinstance(data, list) else []
    
    print(f"  Total trucks: {len(trucks)}")
    for t in trucks[:5]:  # Show first 5
        print(f"    - ID: {t.get('id')}, Plate: {t.get('license_plate')}, Status: {t.get('status')}")
except Exception as e:
    print(f"  Error: {e}")

print("\n2. Getting missions by truck (check if linked to truck)...")
try:
    # Try to find which truck has missions
    req = urllib.request.Request("https://pulsetrack-back.onrender.com/api/v1/missions/TEST-PROD-001/", method="GET")
    req.add_header("Accept", "application/json")
    response = urllib.request.urlopen(req, timeout=10)
    data = json.loads(response.read().decode("utf-8"))
    print(f"  Mission truck_id: {data.get('truck_id')}")
except Exception as e:
    print(f"  Cannot access mission detail: {e}")
