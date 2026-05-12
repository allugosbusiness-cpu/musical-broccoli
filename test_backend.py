import urllib.request
import urllib.error
import ssl

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
    print(f'Response preview: {body[:300]}')
except urllib.error.HTTPError as e:
    print(f'❌ HTTP Error: {e.code} {e.msg}')
except urllib.error.URLError as e:
    print(f'❌ URL Error: {e.reason}')
except Exception as e:
    print(f'❌ Error: {type(e).__name__}: {e}')
