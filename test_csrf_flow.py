import requests
import json

# Test 1: GET request to get CSRF token
print("📍 TEST 1: Fetching trucks list to get CSRF token...")
response = requests.get('http://localhost:8000/api/v1/trucks/')
print(f"Status: {response.status_code}")
print(f"Cookies: {response.cookies.get_dict()}")

if 'csrftoken' in response.cookies:
    csrf_token = response.cookies['csrftoken']
    print(f"✅ CSRF token found: {csrf_token[:20]}...")
    
    # Test 2: Use the token to create a truck
    print("\n📍 TEST 2: Creating truck with CSRF token...")
    headers = {
        'X-CSRFToken': csrf_token,
        'Content-Type': 'application/json'
    }
    
    truck_data = {
        'fleet_id': '99999999-9999-9999-9999-999999999999',
        'truck_identifier': 'CSRF-TEST',
        'plate': 'CSRF-TEST-' + str(int(__import__('time').time())),
        'make': 'TestMake',
        'model': 'TestModel',
        'year': 2024,
        'vin': 'CSRF-VIN',
        'telematics_id': 'CSRF-TEL',
        'fuel_capacity_liters': 100,
        'status': 'IDLE'
    }
    
    response = requests.post(
        'http://localhost:8000/api/v1/trucks/',
        json=truck_data,
        headers=headers,
        cookies=response.cookies  # Include the cookies from first request
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        print("✅ SUCCESS! Truck created with CSRF token!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"❌ Failed with status {response.status_code}")
        print(f"Response: {response.text}")
else:
    print("❌ No CSRF token in cookies")
    print(f"All cookies: {response.cookies}")
