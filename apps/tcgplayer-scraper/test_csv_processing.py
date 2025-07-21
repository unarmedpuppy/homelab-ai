#!/usr/bin/env python3
"""
Test script for CSV processing functionality
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pandas as pd
from tcg import extract_price_from_text, initialize_database, DB_NAME
import sqlite3

def test_csv_loading():
    """Test loading the CSV file"""
    try:
        df = pd.read_csv('export.csv')
        print(f"✓ Successfully loaded CSV with {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        
        # Check for missing URLs
        missing_urls = df[df['url'].isna() | (df['url'] == '')]
        if len(missing_urls) > 0:
            print(f"⚠ Found {len(missing_urls)} entries with missing URLs:")
            for _, row in missing_urls.iterrows():
                print(f"  ID {row['id']}: {row.get('url', 'NO URL')}")
        else:
            print("✓ All entries have valid URLs")
            
        return df
    except Exception as e:
        print(f"✗ Failed to load CSV: {e}")
        return None

def test_database_operations():
    """Test database operations"""
    try:
        initialize_database()
        
        # Test inserting a sample record
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Insert test data
        cursor.execute('''
            INSERT OR REPLACE INTO prices (id, date, product_title, market_price, image_url, url, purchase_date, cost_basis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (999, '2025-01-27', 'Test Product', 123.45, 'test.jpg', 'https://test.com', '2025-01-27', 100.00))
        
        # Query test data
        cursor.execute("SELECT * FROM prices WHERE id = 999")
        result = cursor.fetchone()
        
        if result:
            print("✓ Database operations working correctly")
            print(f"  Test record: {result}")
        else:
            print("✗ Database query failed")
            
        # Clean up test data
        cursor.execute("DELETE FROM prices WHERE id = 999")
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")

def test_cost_basis_processing():
    """Test cost basis processing from CSV"""
    test_cases = [
        ("$379.90", 379.90),
        ("$190.86", 190.86),
        ("$592.45", 592.45),
        ("$155.91", 155.91),
    ]
    
    print("\nTesting cost basis processing:")
    for input_text, expected in test_cases:
        result = extract_price_from_text(input_text)
        status = "✓" if abs(result - expected) < 0.01 else "✗"
        print(f"{status} '{input_text}' -> {result} (expected: {expected})")

if __name__ == "__main__":
    print("CSV Processing Test")
    print("=" * 50)
    
    # Test CSV loading
    df = test_csv_loading()
    
    # Test database operations
    test_database_operations()
    
    # Test cost basis processing
    test_cost_basis_processing()
    
    print("\nTest completed!") 