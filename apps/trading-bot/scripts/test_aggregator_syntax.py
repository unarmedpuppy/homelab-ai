#!/usr/bin/env python3
"""
Quick Syntax Check for Aggregator
==================================

Validates that the aggregator code is syntactically correct and can be imported
when dependencies are available. This is a minimal test that checks structure.
"""

import sys
import ast
from pathlib import Path

def check_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def main():
    """Check aggregator files for syntax errors"""
    project_root = Path(__file__).parent.parent
    aggregator_file = project_root / "src" / "data" / "providers" / "sentiment" / "aggregator.py"
    
    print("=" * 60)
    print("Syntax Check for Sentiment Aggregator")
    print("=" * 60)
    print()
    
    if not aggregator_file.exists():
        print(f"❌ File not found: {aggregator_file}")
        return False
    
    print(f"📄 Checking: {aggregator_file.name}")
    is_valid, error = check_syntax(aggregator_file)
    
    if is_valid:
        print("✅ Syntax is valid")
        print()
        print("Note: This only checks syntax, not runtime dependencies.")
        print("To test with dependencies, run in Docker:")
        print("  docker-compose exec bot python scripts/test_sentiment_aggregator.py")
        return True
    else:
        print(f"❌ Syntax error: {error}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

