import urllib.request, json
url = "https://pulsetrack-back.onrender.com/api/v1/mobile/driver/2ab69512-033c-4bf1-b5cb-0d6b28472af1/available-missions/"
try:
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/json")
    response = urllib.request.urlopen(req, timeout=10)
    data = json.loads(response.read().decode("utf-8"))
    print(f"✓ HTTP 200")
    print(f"  driver_name: {data.get('driver_name')}")
    print(f"  truck_name: {data.get('truck_name')}")
    print(f"  missions count: {data.get('count')}")
    print(f"  missions array length: {len(data.get('missions', []))}")
    if data.get('missions'):
        for m in data['missions']:
            print(f"    - {m.get('mission_id') or m.get('mission_number')}: {m.get('destination')}")
except Exception as e:
    print(f"✗ Error: {e}")
