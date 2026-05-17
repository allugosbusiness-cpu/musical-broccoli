"""
Quick test script to verify dashboard API endpoints are working
Run: python test_dashboard_endpoints.py
"""

import requests
import json

BASE_URL = 'http://localhost:8000/api/v1'

def test_endpoint(method, endpoint, data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {endpoint}")
    print('='*60)
    
    try:
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, json=data or {})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code < 400:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2, default=str)[:500] + "...")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    print("Dashboard API Endpoint Tests")
    print("=" * 60)
    
    tests = [
        ('GET', '/dashboard/summary/'),
        ('GET', '/dashboard/drivers/'),
        ('GET', '/dashboard/trucks/'),
        ('GET', '/dashboard/missions/'),
        ('POST', '/dashboard/recalculate-performance/', {}),
        ('POST', '/dashboard/sync-truck-data/', {}),
    ]
    
    results = {}
    for method, endpoint, *data in tests:
        test_data = data[0] if data else None
        results[endpoint] = test_endpoint(method, endpoint, test_data)
    
    print(f"\n{'='*60}")
    print("Test Summary")
    print('='*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for endpoint, passed_status in results.items():
        status = "✓ PASS" if passed_status else "✗ FAIL"
        print(f"{status}: {endpoint}")
    
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == '__main__':
    main()
