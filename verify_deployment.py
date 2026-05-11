#!/usr/bin/env python3
"""Test activity endpoints after deployment"""
import requests
import json
import time

print("⏳ Waiting for backend to be ready...\n")

base_url = 'https://musical-broccoli-production.up.railway.app/api/v1'
endpoints = [
    ('Activity Summary', f'{base_url}/activities/summary/?days=7'),
    ('Get Activities', f'{base_url}/activities/?days=7&limit=5'),
    ('Critical Activities', f'{base_url}/activities/critical/?days=7'),
]

for attempt in range(3):
    print(f'Attempt {attempt+1}/3...')
    success_count = 0
    
    for name, url in endpoints:
        try:
            resp = requests.get(url, timeout=5)
            status = '✅' if resp.status_code == 200 else f'❌ ({resp.status_code})'
            print(f'  {status} {name}')
            if resp.status_code == 200:
                success_count += 1
        except Exception as e:
            print(f'  ❌ {name}: {str(e)[:40]}')
    
    if success_count == len(endpoints):
        print('\n✅ All endpoints live!')
        break
    elif attempt < 2:
        print(f'   Retrying in 20 seconds...\n')
        time.sleep(20)
