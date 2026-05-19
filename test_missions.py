import urllib.request, json

# Get all missions to see which ones exist
print("Checking all missions...")
try:
    url = "https://pulsetrack-back.onrender.com/api/v1/missions/"
    req = urllib.request.Request(url, method="GET")
    response = urllib.request.urlopen(req, timeout=10)
    data = json.loads(response.read().decode("utf-8"))
    
    missions_list = data["results"] if isinstance(data, dict) and "results" in data else (data if isinstance(data, list) else [])
    
    print(f"? Found {len(missions_list)} total missions")
    
    # Look for MOBTEST missions
    test_missions = [m for m in missions_list if "MOBTEST" in str(m.get("mission_number", m.get("mission_id", "")))]
    print(f"\n  Test missions (MOBTEST): {len(test_missions)}")
    
    for m in test_missions:
        print(f"    • {m.get('mission_number', m.get('mission_id'))}")
        print(f"      Status: {m.get('status')}")
        print(f"      Driver: {m.get('driver')}")
        print(f"      Truck: {m.get('truck')}")
        
except Exception as e:
    print(f"? Error: {e}")
