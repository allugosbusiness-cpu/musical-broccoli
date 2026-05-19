import requests
import json
import time

base_url = 'https://pulsetrack-back.onrender.com/api/v1'
print('='*70)
print('COMPREHENSIVE API ENDPOINT TEST - POST DEFER() FIX')
print('='*70)

endpoints_to_test = [
    ('Dashboard Missions', 'GET', '/dashboard/missions/', None),
    ('Dashboard Drivers', 'GET', '/dashboard/drivers/', None),
    ('Dashboard Trucks', 'GET', '/dashboard/trucks/', None),
    ('Dashboard Summary', 'GET', '/dashboard/summary/', None),
    ('All Missions (REST)', 'GET', '/missions/', None),
    ('All Drivers (REST)', 'GET', '/drivers/', None),
    ('All Trucks (REST)', 'GET', '/trucks/', None),
]

passed = 0
failed = 0

for name, method, path, payload in endpoints_to_test:
    try:
        url = base_url + path
        if method == 'GET':
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f'✓ {name}: HTTP {response.status_code}')
            try:
                data = response.json()
                if isinstance(data, list):
                    print(f'  └─ Returns {len(data)} items')
                elif isinstance(data, dict):
                    if 'missions' in data:
                        print(f'  └─ Contains {len(data.get("missions", []))} missions')
                    elif 'results' in data:
                        print(f'  └─ Contains {len(data.get("results", []))} results')
                    else:
                        print(f'  └─ Keys: {", ".join(list(data.keys())[:5])}...')
            except:
                pass
            passed += 1
        else:
            print(f'✗ {name}: HTTP {response.status_code}')
            failed += 1
    except Exception as e:
        print(f'✗ {name}: {str(e)[:60]}')
        failed += 1

print(f'\n{'='*70}')
print(f'SUMMARY: {passed} passed, {failed} failed')
print('='*70)
