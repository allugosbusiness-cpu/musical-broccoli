import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from django.urls import resolve
from django.http import HttpRequest

# Create a fake request to the URL
request = HttpRequest()
request.path = '/api/v1/trucks/'
request.method = 'GET'

try:
    match = resolve(request.path)
    print(f'URL Pattern: {match.route}')
    print(f'View Name: {match.view_name}')
    print(f'View: {match.func}')
    print(f'App Names: {match.app_names}')
    print(f'Namespace: {match.namespace}')
except Exception as e:
    print(f'Error resolving URL: {e}')
