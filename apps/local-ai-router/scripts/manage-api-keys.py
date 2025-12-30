#!/usr/bin/env python3
"""
CLI tool for managing Local AI Router API keys.

Usage:
    python manage-api-keys.py create <name> [--expires-in-days N] [--scopes SCOPE1,SCOPE2]
    python manage-api-keys.py list [--all]
    python manage-api-keys.py show <id>
    python manage-api-keys.py disable <id>
    python manage-api-keys.py enable <id>
    python manage-api-keys.py delete <id>

Examples:
    # Create a new API key for an agent
    python manage-api-keys.py create "agent-1"
    
    # Create a key that expires in 90 days
    python manage-api-keys.py create "temp-key" --expires-in-days 90
    
    # Create a key with specific scopes
    python manage-api-keys.py create "chat-only" --scopes chat,models
    
    # List all active keys
    python manage-api-keys.py list
    
    # List all keys including disabled
    python manage-api-keys.py list --all
    
    # Disable a key
    python manage-api-keys.py disable 1
    
    # Delete a key permanently
    python manage-api-keys.py delete 1
"""
import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import (
    create_api_key,
    list_api_keys,
    get_api_key_by_id,
    disable_api_key,
    enable_api_key,
    delete_api_key
)
from database import init_database


def format_datetime(dt_str: Optional[str]) -> str:
    """Format datetime string for display."""
    if not dt_str:
        return "Never"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return str(dt_str)


def cmd_create(args):
    """Create a new API key."""
    expires_at = None
    if args.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=args.expires_in_days)
    
    scopes = None
    if args.scopes:
        scopes = [s.strip() for s in args.scopes.split(',')]
    
    full_key, key_id = create_api_key(
        name=args.name,
        scopes=scopes,
        expires_at=expires_at
    )
    
    print(f"\n{'='*60}")
    print(f"API Key Created Successfully!")
    print(f"{'='*60}")
    print(f"\nKey ID:   {key_id}")
    print(f"Name:     {args.name}")
    print(f"Scopes:   {', '.join(scopes) if scopes else 'All'}")
    print(f"Expires:  {expires_at.strftime('%Y-%m-%d %H:%M:%S') if expires_at else 'Never'}")
    print(f"\n{'='*60}")
    print(f"YOUR API KEY (save this - it cannot be retrieved later!):")
    print(f"{'='*60}")
    print(f"\n  {full_key}\n")
    print(f"{'='*60}\n")


def cmd_list(args):
    """List all API keys."""
    keys = list_api_keys(include_disabled=args.all)
    
    if not keys:
        print("No API keys found.")
        return
    
    print(f"\n{'ID':<6} {'Name':<20} {'Prefix':<12} {'Status':<10} {'Created':<20} {'Last Used':<20}")
    print("-" * 90)
    
    for key in keys:
        status = "Active" if key['enabled'] else "Disabled"
        
        # Check if expired
        if key['expires_at']:
            try:
                exp_dt = datetime.fromisoformat(key['expires_at'])
                if exp_dt < datetime.utcnow():
                    status = "Expired"
            except (ValueError, TypeError):
                pass
        
        print(f"{key['id']:<6} {key['name'][:20]:<20} {key['key_prefix']:<12} {status:<10} "
              f"{format_datetime(key['created_at']):<20} {format_datetime(key['last_used_at']):<20}")
    
    print(f"\nTotal: {len(keys)} key(s)")


def cmd_show(args):
    """Show details of a specific API key."""
    key = get_api_key_by_id(args.id)
    
    if not key:
        print(f"Error: API key with id={args.id} not found.")
        sys.exit(1)
    
    print(f"\nAPI Key Details")
    print(f"{'='*40}")
    print(f"ID:           {key['id']}")
    print(f"Name:         {key['name']}")
    print(f"Prefix:       {key['key_prefix']}...")
    print(f"Status:       {'Active' if key['enabled'] else 'Disabled'}")
    print(f"Created:      {format_datetime(key['created_at'])}")
    print(f"Last Used:    {format_datetime(key['last_used_at'])}")
    print(f"Expires:      {format_datetime(key['expires_at'])}")
    print(f"Scopes:       {', '.join(key['scopes']) if key['scopes'] else 'All'}")
    
    if key['metadata']:
        print(f"Metadata:     {key['metadata']}")


def cmd_disable(args):
    """Disable an API key."""
    if disable_api_key(args.id):
        print(f"API key id={args.id} has been disabled.")
    else:
        print(f"Error: API key with id={args.id} not found.")
        sys.exit(1)


def cmd_enable(args):
    """Enable an API key."""
    if enable_api_key(args.id):
        print(f"API key id={args.id} has been enabled.")
    else:
        print(f"Error: API key with id={args.id} not found.")
        sys.exit(1)


def cmd_delete(args):
    """Delete an API key permanently."""
    if not args.force:
        confirm = input(f"Are you sure you want to permanently delete API key id={args.id}? [y/N] ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
    
    if delete_api_key(args.id):
        print(f"API key id={args.id} has been permanently deleted.")
    else:
        print(f"Error: API key with id={args.id} not found.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Manage Local AI Router API keys",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new API key')
    create_parser.add_argument('name', help='Human-readable name for the key')
    create_parser.add_argument('--expires-in-days', type=int, help='Days until key expires')
    create_parser.add_argument('--scopes', help='Comma-separated list of scopes')
    create_parser.set_defaults(func=cmd_create)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all API keys')
    list_parser.add_argument('--all', '-a', action='store_true', help='Include disabled keys')
    list_parser.set_defaults(func=cmd_list)
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show details of an API key')
    show_parser.add_argument('id', type=int, help='API key ID')
    show_parser.set_defaults(func=cmd_show)
    
    # Disable command
    disable_parser = subparsers.add_parser('disable', help='Disable an API key')
    disable_parser.add_argument('id', type=int, help='API key ID')
    disable_parser.set_defaults(func=cmd_disable)
    
    # Enable command
    enable_parser = subparsers.add_parser('enable', help='Enable an API key')
    enable_parser.add_argument('id', type=int, help='API key ID')
    enable_parser.set_defaults(func=cmd_enable)
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Permanently delete an API key')
    delete_parser.add_argument('id', type=int, help='API key ID')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    delete_parser.set_defaults(func=cmd_delete)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize database (ensures tables exist)
    init_database()
    
    # Run the command
    args.func(args)


if __name__ == '__main__':
    main()
