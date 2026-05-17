#!/usr/bin/env python
"""Test Render backend connectivity"""
import urllib.request
import json

try:
    print("Testing Render backend connectivity...")
    print("=" * 60)
    
    # Test API endpoint
    url = 'https://pulsetrack-back.onrender.com/api/v1/'
    print(f"\nEndpoint: {url}")
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            print(f"✓ Status: {status}")
            print(f"✓ Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"✓ Backend is RESPONDING!")
            
            # Try to read response
            data = response.read().decode('utf-8')
            print(f"\nResponse body (first 200 chars):")
            print(data[:200])
            
    except urllib.error.HTTPError as e:
        if e.code in [404, 403, 401]:
            print(f"✓ Status: {e.code} (Expected for API root)")
            print(f"✓ Backend is RESPONDING!")
        else:
            print(f"✗ HTTP Error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        print(f"✗ Connection Error: {e.reason}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"Error: {e}")
