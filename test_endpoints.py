import urllib.request
import json

endpoints_to_test = [
    "https://pulsetrack-back.onrender.com/",
    "https://pulsetrack-back.onrender.com/api/",
    "https://pulsetrack-back.onrender.com/api/v1/",
    "https://pulsetrack-back.onrender.com/api/v1/mobile/",
    "https://pulsetrack-back.onrender.com/api/v1/mobile/driver/719b3a37-b4e0-4355-8b3f-038741647741/",
]

for url in endpoints_to_test:
    try:
        request = urllib.request.Request(url, method="GET")
        request.add_header("Accept", "application/json")
        with urllib.request.urlopen(request, timeout=5) as response:
            print(f"✓ {url}")
            print(f"  Status: {response.status}")
    except urllib.error.HTTPError as e:
        print(f"✗ {url}")
        print(f"  Status: {e.code}")
    except Exception as e:
        print(f"✗ {url}")
        print(f"  Error: {type(e).__name__}")
