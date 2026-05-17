"""
Debug script to capture error details before redeploying
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
os.environ['DEBUG'] = 'True'

django.setup()

from django.test import Client
import json
import traceback

# Use Django test client with DEBUG=True to see detailed errors
client = Client()

try:
    response = client.get('/api/v1/trucks/')
    
    print(f'Status Code: {response.status_code}')
    print(f'Content-Type: {response.get("Content-Type")}')
    
    if response.status_code == 200:
        try:
            data = json.loads(response.content)
            print(f'Success: {data.get("count")} trucks')
        except:
            print(f'Response: {response.content[:200]}')
    else:
        print(f'\n⚠️ Error Response:')
        print(response.content.decode()[:1000])
        if hasattr(response, 'exc_info') and response.exc_info:
            print(f'\n⚠️ Exception:')
            traceback.print_exception(*response.exc_info)
        
except Exception as e:
    print(f'❌ Exception: {e}')
    traceback.print_exc()
