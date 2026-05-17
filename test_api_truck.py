import requests
import json
import uuid
from datetime import datetime

API_URL = 'http://localhost:8000/api/v1'

truck_data = {
    'fleet_id': str(uuid.uuid4()),
    'truck_identifier': 'TEST-API-TRUCK',
    'plate': 'TEST-API-' + str(int(datetime.now().timestamp())),
    'make': 'TestMake',
    'model': 'TestModel',
    'year': 2024,
    'vin': 'TEST-VIN-' + str(int(datetime.now().timestamp())),
    'telematics_id': 'TEST-TEL',
    'fuel_capacity_liters': 100,
    'status': 'IDLE'
}

print('📤 Sending truck creation request to:', f"{API_URL}/trucks/")
print('📋 Data:', json.dumps(truck_data, indent=2))

try:
    response = requests.post(
        f"{API_URL}/trucks/",
        json=truck_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    print(f'\n✅ Success! Status: {response.status_code}')
    print('📦 Response data:')
    print(json.dumps(response.json(), indent=2))
    print(f'\nTruck created with ID: {response.json().get("fleet_id")}')
    
except requests.exceptions.RequestException as error:
    print('\n❌ Error creating truck')
    print(f'  Message: {error}')
    if hasattr(error, 'response') and error.response is not None:
        print(f'  Status: {error.response.status_code}')
        print(f'  Status Text: {error.response.reason}')
        try:
            print('  Response Data:', json.dumps(error.response.json(), indent=2))
        except:
            print('  Response Text:', error.response.text)
