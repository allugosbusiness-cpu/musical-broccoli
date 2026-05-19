import urllib.request, json

print("1. Getting mission by UUID...")
try:
    req = urllib.request.Request("https://pulsetrack-back.onrender.com/api/v1/missions/33d72cc0-1254-4a3f-a144-328a3fdbb9ac/", method="GET")
    req.add_header("Accept", "application/json")
    response = urllib.request.urlopen(req, timeout=10)
    data = json.loads(response.read().decode("utf-8"))
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"  Error: {e}")

print("\n2. Checking available-missions endpoint structure...")
try:
    req = urllib.request.Request("https://pulsetrack-back.onrender.com/api/v1/mobile/driver/2ab69512-033c-4bf1-b5cb-0d6b28472af1/available-missions/", method="GET")
    req.add_header("Accept", "application/json")
    response = urllib.request.urlopen(req, timeout=10)
    data = json.loads(response.read().decode("utf-8"))
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"  Error: {e}")
