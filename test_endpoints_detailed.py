#!/usr/bin/env python
"""
Test actual API endpoints to see detailed error messages
"""
import urllib.request
import urllib.error
import json

endpoints = [
    'https://web-production-691ff.up.railway.app/',
    'https://web-production-691ff.up.railway.app/api/v1/dashboard/trucks/',
    'https://web-production-691ff.up.railway.app/admin/',
]

print("=" * 80)
print("TESTING RAILWAY BACKEND ENDPOINTS")
print("=" * 80)

for endpoint in endpoints:
    print(f"\n\nTesting: {endpoint}")
    print("-" * 80)
    
    try:
        req = urllib.request.Request(
            endpoint,
            headers={'User-Agent': 'Python-Diagnostic-Bot'}
        )
        response = urllib.request.urlopen(req)
        status = response.status
        content = response.read().decode('utf-8')
        
        print(f"Status: {status}")
        print(f"Headers:")
        for header, value in response.headers.items():
            print(f"  {header}: {value}")
        
        print(f"\nResponse preview (first 500 chars):")
        print(content[:500])
        
    except urllib.error.HTTPError as e:
        print(f"Status: {e.code}")
        print(f"Reason: {e.reason}")
        print(f"Headers:")
        for header, value in e.headers.items():
            print(f"  {header}: {value}")
        
        try:
            error_body = e.read().decode('utf-8')
            print(f"\nError response (first 1000 chars):")
            print(error_body[:1000])
            
            # Try to extract useful error info
            if 'Traceback' in error_body:
                print("\n✓ Found traceback in response!")
                # Extract lines around 'Traceback'
                lines = error_body.split('\n')
                for i, line in enumerate(lines):
                    if 'Traceback' in line or 'Error' in line or 'Exception' in line:
                        start = max(0, i - 2)
                        end = min(len(lines), i + 15)
                        print("\n--- Traceback context ---")
                        print('\n'.join(lines[start:end]))
                        break
        except Exception as read_err:
            print(f"Could not read error body: {read_err}")
    
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 80)
print("ENDPOINT TESTING COMPLETE")
print("=" * 80)
