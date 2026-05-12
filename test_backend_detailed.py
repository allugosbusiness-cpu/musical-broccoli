import urllib.request
import urllib.error
import ssl
import json

url = 'https://web-production-691ff.up.railway.app/api/v1/dashboard/trucks/'
req = urllib.request.Request(url, method='GET')

try:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    response = urllib.request.urlopen(req, context=context, timeout=10)
    print(f'✅ Backend is reachable!')
    print(f'Status: {response.code}')
    body = response.read().decode('utf-8')
    print(f'Response: {body}')
except urllib.error.HTTPError as e:
    print(f'❌ HTTP Error: {e.code} {e.msg}')
    print(f'Error Body:')
    error_body = e.read().decode('utf-8')
    print(error_body[:500])
except urllib.error.URLError as e:
    print(f'❌ URL Error: {e.reason}')
except Exception as e:
    print(f'❌ Error: {type(e).__name__}: {e}')

# Also test health endpoint
print("\n" + "="*50)
print("Testing health endpoint...")
url2 = 'https://web-production-691ff.up.railway.app/health/'
req2 = urllib.request.Request(url2, method='GET')

try:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    response = urllib.request.urlopen(req2, context=context, timeout=10)
    print(f'✅ Health endpoint responded!')
    print(f'Status: {response.code}')
    body = response.read().decode('utf-8')
    print(f'Response: {body}')
except urllib.error.HTTPError as e:
    print(f'❌ HTTP Error: {e.code}')
except Exception as e:
    print(f'❌ Error: {type(e).__name__}: {e}')
