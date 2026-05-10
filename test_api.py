import requests
import json

url = 'http://192.168.1.236:8000/api/v1/mobile/driver-registration/'
data = {
    'qr_data': json.dumps({
        'type': 'truck_registration',
        'truck_id': '1bea7139-5cac-4b17-8ccb-f1ac26217692',
        'truck_identifier': 'Test Truck'
    }),
    'phone_number': '1234567890'
}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
