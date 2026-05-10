import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
os.environ['DEBUG'] = 'True'
django.setup()

from django.test import Client
import json

# Use Django test client to simulate HTTP request
client = Client()
response = client.get('/api/v1/trucks/')

print(f'Status Code: {response.status_code}')
print(f'Content-Type: {response.get("Content-Type")}')
print(f'Response Length: {len(response.content)}')

if response.status_code != 200:
    print(f'\nResponse Content:\n{response.content.decode()}')
else:
    try:
        data = json.loads(response.content)
        print(f'\nResponse Data:')
        print(f'- Count: {data.get("count")}')
        print(f'- Results: {len(data.get("results", []))} items')
        if data.get('results'):
            print(f'- First truck: {data["results"][0].get("truck_identifier")}')
    except Exception as e:
        print(f'Error parsing response: {e}')
