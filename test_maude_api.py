#!/usr/bin/env python3
"""
Quick test script for MAUDE API
Tests various query patterns to show what works
"""

import requests
import json

def test_query(query, description):
    """Test a single query and print results"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Query: {query}")
    print('-'*60)
    
    url = "https://api.fda.gov/device/event.json"
    params = {
        'search': query,
        'limit': 5
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        total = data['meta']['results']['total']
        retrieved = len(data['results'])
        
        print(f"✓ SUCCESS")
        print(f"  Total matching reports: {total:,}")
        print(f"  Retrieved: {retrieved}")
        
        if retrieved > 0:
            first = data['results'][0]
            print(f"\n  Sample report:")
            print(f"    Report #: {first.get('report_number', 'N/A')}")
            print(f"    Event type: {first.get('event_type', 'N/A')}")
            print(f"    Date received: {first.get('date_received', 'N/A')}")
            if 'device' in first and len(first['device']) > 0:
                device = first['device'][0]
                print(f"    Device: {device.get('generic_name', 'N/A')}")
                print(f"    Manufacturer: {device.get('manufacturer_d_name', 'N/A')}")
        
        return True
        
    except requests.exceptions.HTTPError as e:
        print(f"✗ FAILED: HTTP {response.status_code}")
        if response.status_code == 500:
            print("  → This query is too broad or complex for the API")
            print("  → Try narrowing the search criteria")
        return False
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("MAUDE API Query Tests")
    print("="*60)
    
    # Test various query patterns
    tests = [
        # These should work
        ('device.generic_name:"pacemaker"', 
         'Simple device search'),
        
        ('device.manufacturer_d_name:"medtronic"', 
         'Manufacturer search'),
        
        ('event_type:"Death"', 
         'Event type search'),
        
        ('device.brand_name:"freestyle"', 
         'Brand name search'),
        
        ('device.generic_name:"insulin+pump"+AND+event_type:"Injury"', 
         'Combined device + event type'),
        
        ('device.generic_name:"pacemaker"+AND+date_received:[20240101+TO+20240131]', 
         'Device + date range (1 month)'),
        
        # This might fail (too broad)
        ('date_received:[20230101+TO+20231231]', 
         'Broad date range (may fail)'),
    ]
    
    results = []
    for query, desc in tests:
        success = test_query(query, desc)
        results.append((desc, success))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print()
    for desc, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {desc}")
    
    print("\n" + "="*60)
    print("KEY TAKEAWAYS:")
    print("  • Device-specific queries work best")
    print("  • Combine date ranges WITH device/manufacturer filters")
    print("  • Avoid searching by date alone for broad ranges")
    print("  • Start specific, then broaden if needed")
    print("="*60)
