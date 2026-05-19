import urllib.request
import json

url = "https://pulsetrack-back.onrender.com/api/v1/mobile/driver/719b3a37-b4e0-4355-8b3f-038741647741/available-missions/"

try:
    request = urllib.request.Request(url, method="GET")
    request.add_header("Accept", "application/json")
    
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
        print("✓ SUCCESS! Status 200")
        print(f"  truck_name: {data.get('truck_name')}")
        print(f"  driver_name: {data.get('driver_name')}")
        print(f"  missions: {data.get('count')}")
            
except urllib.error.HTTPError as e:
    print(f"✗ HTTP {e.code} - Render still deploying or endpoint not found")
except Exception as e:
    print(f"✗ Error: {e}")
