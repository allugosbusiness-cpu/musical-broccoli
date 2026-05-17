import urllib.request
import ssl

# Test admin page
url = 'https://web-production-691ff.up.railway.app/admin/'
req = urllib.request.Request(url, method='GET')

try:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    response = urllib.request.urlopen(req, context=context, timeout=10)
    print(f'✅ Admin page responded: {response.code}')
    body = response.read().decode('utf-8')
    print(f'Response preview (first 500 chars):\n{body[:500]}')
except urllib.error.HTTPError as e:
    print(f'❌ HTTP Error: {e.code}')
    print(f'Error headers: {dict(e.headers)}')
except Exception as e:
    print(f'❌ Error: {type(e).__name__}: {e}')

# Also test a simple health check that doesn't need DB
print("\n" + "="*50)
url2 = 'https://web-production-691ff.up.railway.app/'
req2 = urllib.request.Request(url2, method='GET')

try:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    response = urllib.request.urlopen(req2, context=context, timeout=10)
    print(f'✅ Root URL responded: {response.code}')
    body = response.read().decode('utf-8')
    print(f'Response preview: {body[:300]}')
except urllib.error.HTTPError as e:
    print(f'❌ HTTP Error: {e.code}')
except Exception as e:
    print(f'❌ Error: {type(e).__name__}: {e}')
