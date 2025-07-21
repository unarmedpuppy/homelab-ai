#!/usr/bin/env python3
"""
Test script for TCGPlayer price scraper
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from tcg import get_tcgplayer_price, extract_price_from_text

def test_price_extraction():
    """Test the price extraction function"""
    test_cases = [
        ("$123.45", 123.45),
        ("$1,234.56", 1234.56),
        ("$1,234", 1234.0),
        ("123.45", 123.45),
        ("1,234.56", 1234.56),
        ("$0.00", 0.0),
        ("", 0.0),
        ("N/A", 0.0),
    ]
    
    print("Testing price extraction...")
    for input_text, expected in test_cases:
        result = extract_price_from_text(input_text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_text}' -> {result} (expected: {expected})")

def test_single_url():
    """Test scraping a single URL"""
    test_url = "https://www.tcgplayer.com/product/236348/Magic-Modern%20Horizons%202-Modern%20Horizons%202%20Collector%20Booster%20Display?Language=English"
    
    print(f"\nTesting URL: {test_url}")
    title, price, image_url = get_tcgplayer_price(test_url)
    
    print(f"Title: {title}")
    print(f"Price: {price}")
    print(f"Image URL: {image_url}")

if __name__ == "__main__":
    print("TCGPlayer Scraper Test")
    print("=" * 50)
    
    # Test price extraction
    test_price_extraction()
    
    # Test single URL (uncomment to test actual scraping)
    # test_single_url()
    
    print("\nTest completed!") 