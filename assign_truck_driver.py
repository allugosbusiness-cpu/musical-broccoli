import urllib.request, json

# Get first truck ID
truck_id = "d16aaa81-1bba-4a20-b76f-ab8d23ed71f3"

print(f"Assigning truck {truck_id} to driver...")
try:
    data = json.dumps({"truck": truck_id}).encode("utf-8")
    req = urllib.request.Request(
        "https://pulsetrack-back.onrender.com/api/v1/drivers/2ab69512-033c-4bf1-b5cb-0d6b28472af1/",
        data=data,
        method="PATCH",
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    response = urllib.request.urlopen(req, timeout=10)
    result = json.loads(response.read().decode("utf-8"))
    print(f"✓ Success!")
    print(f"  Driver truck: {result.get('truck')}")
except urllib.error.HTTPError as e:
    print(f"✗ HTTP Error {e.code}")
    print(f"  {e.read().decode('utf-8')}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n\nNow assigning the mission to the truck and driver...")
try:
    data = json.dumps({
        "truck": truck_id,
        "driver": "2ab69512-033c-4bf1-b5cb-0d6b28472af1"
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://pulsetrack-back.onrender.com/api/v1/missions/33d72cc0-1254-4a3f-a144-328a3fdbb9ac/",
        data=data,
        method="PATCH",
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    response = urllib.request.urlopen(req, timeout=10)
    result = json.loads(response.read().decode("utf-8"))
    print(f"✓ Success!")
    print(f"  Mission truck: {result.get('truck')}")
    print(f"  Mission driver: {result.get('driver')}")
except urllib.error.HTTPError as e:
    print(f"✗ HTTP Error {e.code}")
    print(f"  {e.read().decode('utf-8')}")
except Exception as e:
    print(f"✗ Error: {e}")
