import urllib.request, json

print("Getting full driver response...")
try:
    req = urllib.request.Request("https://pulsetrack-back.onrender.com/api/v1/drivers/2ab69512-033c-4bf1-b5cb-0d6b28472af1/", method="GET")
    req.add_header("Accept", "application/json")
    response = urllib.request.urlopen(req, timeout=10)
    data = json.loads(response.read().decode("utf-8"))
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n\nGetting full mission response (one example)...")
try:
    req = urllib.request.Request("https://pulsetrack-back.onrender.com/api/v1/missions/TEST-PROD-001/", method="GET")
    req.add_header("Accept", "application/json")
    response = urllib.request.urlopen(req, timeout=10)
    data = json.loads(response.read().decode("utf-8"))
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")
