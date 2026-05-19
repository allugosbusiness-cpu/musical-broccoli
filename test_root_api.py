import urllib.request
import json

url = "https://pulsetrack-back.onrender.com/api/v1/"

try:
    request = urllib.request.Request(url, method="GET")
    request.add_header("Accept", "application/json")
    with urllib.request.urlopen(request, timeout=5) as response:
        data = response.read().decode("utf-8")
        print("Response from /api/v1/:")
        print(data[:1000])
except Exception as e:
    print(f"Error: {e}")
