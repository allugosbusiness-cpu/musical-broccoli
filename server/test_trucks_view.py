#!/usr/bin/env python
"""
Test script to debug trucks endpoint
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from api.views_v2 import TruckViewSet
import json

factory = APIRequestFactory()
request = factory.get('/api/v1/trucks/')

view = TruckViewSet.as_view({'get': 'list'})

try:
    response = view(request)
    print(f'✅ Status: {response.status_code}')
    if response.status_code == 200:
        print(f'Data: {json.dumps(response.data, indent=2, default=str)}')
    else:
        print(f'Response: {response.data}')
except Exception as e:
    import traceback
    print(f'❌ Error: {e}')
    print('Traceback:')
    traceback.print_exc()
