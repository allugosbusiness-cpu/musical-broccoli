import requests
import json

base_url = 'https://pulsetrack-back.onrender.com/api/v1'
print('='*70)
print('FINAL COMPREHENSIVE VERIFICATION TEST')
print('='*70)

tests = {
    'Core Dashboard APIs': [
        ('✓ Health Check', 'GET', '/health/', 200),
        ('✓ Dashboard Missions', 'GET', '/dashboard/missions/', 200),
        ('✓ Dashboard Drivers', 'GET', '/dashboard/drivers/', 200),
        ('✓ Dashboard Trucks', 'GET', '/dashboard/trucks/', 200),
        ('✓ Dashboard Summary', 'GET', '/dashboard/summary/', 200),
    ],
    'Mobile APIs': [
        ('✓ Mobile Driver Registration', 'POST', '/mobile/driver/register/', [201, 400]),
        ('✓ Mobile Available Missions', 'GET', '/mobile/driver/test-driver-uuid/available-missions/', [200, 404]),
    ],
    'REST APIs': [
        ('✓ Missions List', 'GET', '/missions/', 200),
        ('✓ Drivers List', 'GET', '/drivers/', 200),
        ('✓ Trucks List', 'GET', '/trucks/', 200),
    ]
}

print('\nAPI ENDPOINT VERIFICATION:')
print('='*70)

all_passed = True
for category, endpoints in tests.items():
    print(f'\n{category}:')
    for name, method, path, expected_status in endpoints:
        try:
            url = base_url + path
            if method == 'GET':
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, json={}, timeout=10)
            
            expected = [expected_status] if isinstance(expected_status, int) else expected_status
            if response.status_code in expected:
                print(f'  {name} - HTTP {response.status_code}')
            else:
                print(f'  ✗ FAILED: {name} - Got HTTP {response.status_code}, expected {expected}')
                all_passed = False
        except Exception as e:
            print(f'  ✗ ERROR: {name} - {str(e)[:40]}')
            all_passed = False

print(f'\n{'='*70}')
if all_passed:
    print('✓✓✓ ALL CRITICAL ENDPOINTS VERIFIED AND WORKING ✓✓✓')
else:
    print('⚠ Some endpoints had issues - check above')
print('='*70)

# Get specific data for verification
print('\n' + '='*70)
print('DATA VERIFICATION:')
print('='*70)

try:
    missions = requests.get(f'{base_url}/dashboard/missions/', timeout=10).json()
    print(f'✓ Missions Available: {len(missions)} total')
    if missions:
        sample = missions[0]
        print(f'  Sample mission fields: mission_number={sample.get("mission_number")}, status={sample.get("status")}, truck_name={sample.get("truck_name")}, driver_name={sample.get("driver_name")}')
        
    drivers = requests.get(f'{base_url}/dashboard/drivers/', timeout=10).json()
    print(f'✓ Drivers Available: {len(drivers)} total')
    
    trucks = requests.get(f'{base_url}/dashboard/trucks/', timeout=10).json()
    print(f'✓ Trucks Available: {len(trucks)} total')
    
    summary = requests.get(f'{base_url}/dashboard/summary/', timeout=10).json()
    print(f'✓ Summary: {summary.get("total_missions")} missions, {summary.get("total_drivers")} drivers, {summary.get("total_trucks")} trucks')
    
except Exception as e:
    print(f'✗ Error fetching data: {str(e)}')

print('='*70)
