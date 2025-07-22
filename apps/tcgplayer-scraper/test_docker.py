#!/usr/bin/env python3
"""
Test script for Docker container functionality
"""

import requests
import time
import sys

def test_web_interface():
    """Test if the web interface is accessible"""
    base_url = "http://localhost:5000"
    
    print("Testing web interface...")
    
    try:
        # Test main page
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"Main page status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Main page accessible")
        else:
            print("✗ Main page not accessible")
            
        # Test sealed products page
        response = requests.get(f"{base_url}/sealed-products", timeout=10)
        print(f"Sealed products page status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Sealed products page accessible")
        else:
            print("✗ Sealed products page not accessible")
            
        # Test API endpoint
        response = requests.get(f"{base_url}/api/prices", timeout=10)
        print(f"API endpoint status: {response.status_code}")
        if response.status_code == 200:
            print("✓ API endpoint accessible")
            data = response.json()
            print(f"  Found {len(data.get('data', []))} price records")
        else:
            print("✗ API endpoint not accessible")
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to web interface - container may not be running")
    except Exception as e:
        print(f"✗ Error testing web interface: {e}")

def test_database():
    """Test database functionality"""
    try:
        from tcg import initialize_database, DB_NAME
        import sqlite3
        
        print("\nTesting database...")
        initialize_database()
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM prices")
        count = cursor.fetchone()[0]
        print(f"✓ Database accessible with {count} records")
        conn.close()
        
    except Exception as e:
        print(f"✗ Database error: {e}")

if __name__ == "__main__":
    print("Docker Container Test")
    print("=" * 50)
    
    test_web_interface()
    test_database()
    
    print("\nTest completed!") 