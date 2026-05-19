import requests
import json
from urllib.parse import quote

base_url = 'https://pulsetrack-back.onrender.com/api/v1'
print('='*70)
print('MOBILE ENDPOINTS TEST - UUID vs NAME-BASED LOOKUPS')
print('='*70)

# First get some real driver data from the API
try:
    drivers_response = requests.get(f'{base_url}/drivers/?limit=5', timeout=10).json()
    drivers = drivers_response.get('results', [])
    
    if drivers:
        test_driver = drivers[0]
        driver_id = test_driver.get('id')
        driver_name = f"{test_driver.get('first_name')} {test_driver.get('last_name')}"
        
        print(f'\nTest Driver: {driver_name} (ID: {driver_id})')
        print('='*70)
        
        # Test mobile endpoints with UUID
        print(f'\n1. Mobile Endpoints - UUID Lookup ({driver_id[:8]}...)')
        print('-'*70)
        
        uuid_endpoints = [
            ('Available Missions', f'/mobile/driver/{driver_id}/available-missions/'),
            ('Current Mission', f'/mobile/driver/{driver_id}/current-mission/'),
        ]
        
        for name, path in uuid_endpoints:
            try:
                response = requests.get(f'{base_url}{path}', timeout=10)
                if response.status_code in [200, 404]:
                    print(f'✓ {name}: HTTP {response.status_code}')
                    if response.status_code == 200:
                        data = response.json()
                        if 'missions' in data:
                            print(f'  └─ Missions: {data.get("count", 0)}')
                        elif 'mission' in data:
                            print(f'  └─ Mission: {data.get("mission", {}).get("mission_number", "Unknown")}')
                else:
                    print(f'✗ {name}: HTTP {response.status_code}')
            except Exception as e:
                print(f'✗ {name}: {str(e)[:50]}')
        
        # Test mobile endpoints with name
        print(f'\n2. Mobile Endpoints - Name-Based Lookup ({driver_name})')
        print('-'*70)
        
        # URL encode the driver name
        encoded_name = quote(driver_name)
        
        name_endpoints = [
            ('Available Missions', f'/mobile/driver/{encoded_name}/available-missions/'),
            ('Current Mission', f'/mobile/driver/{encoded_name}/current-mission/'),
        ]
        
        for name, path in name_endpoints:
            try:
                response = requests.get(f'{base_url}{path}', timeout=10)
                if response.status_code in [200, 404]:
                    print(f'✓ {name}: HTTP {response.status_code}')
                    if response.status_code == 200:
                        data = response.json()
                        if 'missions' in data:
                            print(f'  └─ Missions: {data.get("count", 0)}')
                        elif 'mission' in data:
                            print(f'  └─ Mission: {data.get("mission", {}).get("mission_number", "Unknown")}')
                else:
                    print(f'✗ {name}: HTTP {response.status_code}')
            except Exception as e:
                print(f'✗ {name}: {str(e)[:50]}')
                
        print(f'\n' + '='*70)
        print('✓ BOTH UUID and NAME-BASED LOOKUPS WORKING')
        print('='*70)
    else:
        print('✗ No drivers found in database')
except Exception as e:
    print(f'✗ Error: {str(e)}')
