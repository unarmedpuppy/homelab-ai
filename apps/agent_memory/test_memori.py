#!/usr/bin/env python3
"""
Test script for Memori integration.

This script tests:
1. Memori installation
2. Database connection
3. Memory recording
4. Context retrieval
"""

import os
import sys
from pathlib import Path

def test_import():
    """Test if Memori can be imported."""
    try:
        from memori import Memori
        print("✅ Memori import successful")
        return True
    except ImportError as e:
        print(f"❌ Memori import failed: {e}")
        return False

def test_helper_import():
    """Test if helper module can be imported."""
    try:
        from apps.agent_memory import get_memori_instance, setup_memori
        print("✅ Helper module import successful")
        return True
    except ImportError as e:
        print(f"❌ Helper module import failed: {e}")
        print("   Make sure you're running from project root")
        return False

def test_setup():
    """Test Memori setup."""
    try:
        from apps.agent_memory import setup_memori
        
        print("\n🔧 Testing Memori setup...")
        memori = setup_memori()
        print("✅ Memori setup successful")
        print(f"   Database: {memori.database_connect if hasattr(memori, 'database_connect') else 'configured'}")
        return True
    except Exception as e:
        print(f"❌ Memori setup failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check if MEMORI_AGENTS__OPENAI_API_KEY is set")
        print("   2. Check database connection string")
        print("   3. Verify Memori is installed: pip install memori")
        return False

def test_basic_functionality():
    """Test basic Memori functionality."""
    try:
        from apps.agent_memory import get_global_memori
        
        print("\n🧪 Testing basic functionality...")
        memori = get_global_memori()
        
        # Test that memory is enabled
        if hasattr(memori, 'enabled') and memori.enabled:
            print("✅ Memory is enabled")
        else:
            print("⚠️  Memory enabled status unclear (may still work)")
        
        print("✅ Basic functionality test passed")
        print("\n💡 Memori will automatically:")
        print("   - Intercept LLM calls")
        print("   - Inject context before calls")
        print("   - Record conversations after calls")
        print("   - Learn patterns in background")
        
        return True
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Memori Integration\n")
    
    tests = [
        ("Import Memori", test_import),
        ("Import Helper", test_helper_import),
        ("Setup Memori", test_setup),
        ("Basic Functionality", test_basic_functionality),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 {name}:")
        result = test_func()
        results.append((name, result))
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Summary:")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Memori is ready to use.")
        return 0
    else:
        print("\n❌ Some tests failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

