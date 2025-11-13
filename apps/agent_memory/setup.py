#!/usr/bin/env python3
"""
Setup script for Memori agent memory system.

This script:
1. Checks if Memori is installed
2. Sets up database (SQLite by default, or PostgreSQL if configured)
3. Tests the connection
4. Creates initial configuration
"""

import os
import sys
from pathlib import Path

def check_memori_installed():
    """Check if Memori is installed."""
    try:
        import memori
        print("✅ Memori is installed")
        try:
            print(f"   Version: {memori.__version__}")
        except:
            pass
        return True
    except ImportError:
        print("❌ Memori is not installed")
        print("\n   Installation options:")
        print("   1. User install: python3 -m pip install --user memori")
        print("   2. Virtual env: python3 -m venv venv && source venv/bin/activate && pip install memori")
        print("   3. See: apps/agent_memory/INSTALL.md for details")
        return False

def setup_database():
    """Setup database connection."""
    # Check for PostgreSQL connection string
    pg_conn = os.getenv("MEMORI_DATABASE__CONNECTION_STRING")
    
    if pg_conn and pg_conn.startswith("postgresql://"):
        print(f"✅ Using PostgreSQL: {pg_conn.split('@')[1] if '@' in pg_conn else 'configured'}")
        return pg_conn
    else:
        # Use SQLite by default
        db_path = Path(__file__).parent / "agent_memory.db"
        sqlite_conn = f"sqlite:///{db_path.absolute()}"
        print(f"✅ Using SQLite: {db_path}")
        return sqlite_conn

def test_memori():
    """Test Memori setup."""
    try:
        from apps.agent_memory import setup_memori
        
        print("\n🔧 Setting up Memori...")
        memori = setup_memori()
        
        print("✅ Memori is configured and enabled")
        print("   Memory will automatically:")
        print("   - Inject context before LLM calls")
        print("   - Record all conversations")
        print("   - Learn patterns in background")
        
        return True
    except Exception as e:
        print(f"❌ Error setting up Memori: {e}")
        return False

def create_env_template():
    """Create .env template if it doesn't exist."""
    env_template = """# Memori Configuration
# Uncomment and configure if using PostgreSQL
# MEMORI_DATABASE__CONNECTION_STRING="postgresql://user:pass@localhost/memori"

# OpenAI API Key (required for Memori)
# MEMORI_AGENTS__OPENAI_API_KEY="sk-..."

# Memory namespace (default: home-server)
# MEMORI_MEMORY__NAMESPACE="home-server"
"""
    
    env_file = Path(__file__).parent / ".env.template"
    if not env_file.exists():
        env_file.write_text(env_template)
        print(f"✅ Created .env.template at {env_file}")
    else:
        print(f"ℹ️  .env.template already exists at {env_file}")

def main():
    """Main setup function."""
    print("🚀 Setting up Memori Agent Memory System\n")
    
    # Check installation
    if not check_memori_installed():
        sys.exit(1)
    
    # Setup database
    db_conn = setup_database()
    print(f"   Database: {db_conn}\n")
    
    # Create env template
    create_env_template()
    print()
    
    # Test setup
    if test_memori():
        print("\n✅ Memori setup complete!")
        print("\n📝 Next steps:")
        print("   1. Set MEMORI_AGENTS__OPENAI_API_KEY environment variable")
        print("   2. (Optional) Configure PostgreSQL in .env")
        print("   3. Import and use: from apps.agent_memory import setup_memori")
        print("   4. Call: memori = setup_memori()")
        return 0
    else:
        print("\n❌ Setup failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

