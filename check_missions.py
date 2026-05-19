import urllib.request, json

# Get all missions to see which ones exist
print("Checking all missions...")
try:
    url = "https://pulsetrack-back.onrender.com/api/v1/missions/"
    req = urllib.request.Request(url, method="GET")
    response = urllib.request.urlopen(req, timeout=10)
    data = json.loads(response.read().decode("utf-8"))
    
    missions_list = data["results"] if isinstance(data, dict) and "results" in data else (data if isinstance(data, list) else [])
    
    print("Found {} total missions".format(len(missions_list)))
    
    # Look for MOBTEST missions
    test_missions = [m for m in missions_list if "MOBTEST" in str(m.get("mission_number", m.get("mission_id", "")))]
    print("Test missions (MOBTEST): {}".format(len(test_missions)))
    
    for m in test_missions:
        print("  - {}".format(m.get('mission_number', m.get('mission_id'))))
        print("    Status: {}".format(m.get('status')))
        print("    Driver: {}".format(m.get('driver')))
        print("    Truck: {}".format(m.get('truck')))
        
except Exception as e:
    print("Error: {}".format(e))
