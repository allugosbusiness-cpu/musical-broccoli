import requests

base_url = 'https://musical-broccoli-production.up.railway.app/api/v1'

endpoints = [
    '/trucks/',
    '/dashboard/trucks/',
    '/dashboard/summary/',
    '/dashboard/drivers/',
    '/dashboard/missions/',
]

for ep in endpoints:
    try:
        r = requests.get(f'{base_url}{ep}', timeout=10)
        print(f'{ep}: Status {r.status_code}', end='')
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and 'results' in data:
                print(f' - Items: {len(data["results"])}')
            elif isinstance(data, dict):
                print(f' - Keys: {list(data.keys())[:3]}')
            elif isinstance(data, list):
                print(f' - Items: {len(data)}')
            else:
                print(f' - OK')
        else:
            error_msg = r.text[:80] if r.text else 'No error message'
            print(f' - Error: {error_msg}')
    except Exception as e:
        print(f'{ep}: Exception - {str(e)[:60]}')
