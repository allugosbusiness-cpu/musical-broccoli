import requests

headers = {
    'Accept': 'application/json',
    'User-Agent': 'Python-Test'
}

try:
    r = requests.get('https://musical-broccoli-production.up.railway.app/api/v1/trucks/', headers=headers, timeout=10)
    print(f'Status: {r.status_code}')
    print(f'Content-Type: {r.headers.get("content-type")}')
    print(f'Body length: {len(r.text)}')
    print(f'First 500 chars:\n{r.text[:500]}')
    if r.status_code != 200:
        print(f'\nFull Response:\n{r.text}')
except Exception as e:
    import traceback
    print(f'Error: {e}')
    traceback.print_exc()
