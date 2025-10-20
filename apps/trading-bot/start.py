#!/usr/bin/env python3
"""
Trading Bot Startup Script
==========================

Simple script to start the trading bot with proper setup.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if requirements are installed"""
    try:
        import fastapi
        import uvicorn
        import yfinance
        import sqlalchemy
        print("✅ Core requirements installed")
        return True
    except ImportError as e:
        print(f"❌ Missing requirement: {e}")
        print("Please run: pip install -r requirements/base.txt")
        return False

def setup_environment():
    """Setup environment file if it doesn't exist"""
    env_file = Path(".env")
    env_template = Path("env.template")
    
    if not env_file.exists() and env_template.exists():
        print("📝 Creating .env file from template...")
        env_file.write_text(env_template.read_text())
        print("✅ .env file created")
        print("⚠️  Please edit .env file with your API keys")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  No .env file found, using defaults")

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "data", "migrations/versions"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")

def run_quick_test():
    """Run quick test to verify setup"""
    print("🧪 Running quick test...")
    
    try:
        result = subprocess.run([
            sys.executable, "scripts/quick_test.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Quick test passed")
            return True
        else:
            print(f"❌ Quick test failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Quick test timed out")
        return False
    except Exception as e:
        print(f"❌ Quick test error: {e}")
        return False

def start_server():
    """Start the API server"""
    print("🚀 Starting Trading Bot API server...")
    print("📱 Open http://localhost:8000 in your browser")
    print("🧪 Test page: http://localhost:8000/test")
    print("📚 API docs: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        subprocess.run([
            sys.executable, "main.py"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

def main():
    """Main startup function"""
    print("🤖 Trading Bot Startup")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        return False
    
    # Setup environment
    setup_environment()
    
    # Create directories
    create_directories()
    
    # Run quick test
    if not run_quick_test():
        print("⚠️  Quick test failed, but continuing...")
    
    # Start server
    start_server()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
