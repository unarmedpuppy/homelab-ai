#!/usr/bin/env python3
"""
Helper script to find Telegram channel names and IDs.
Run this to discover channel information for your .env file.
"""

import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat

load_dotenv()

# Get credentials from .env
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")

if not API_ID or not API_HASH:
    print("❌ Please set API_ID and API_HASH in your .env file first")
    print("Get them from: https://my.telegram.org/apps")
    exit(1)

print("💡 TIP: You can now specify multiple channels in your .env file:")
print("   CHANNELS=@channel1,@channel2,-1001234567890")
print()

async def find_channels():
    """Find all channels and groups you have access to"""
    async with TelegramClient("temp_session", API_ID, API_HASH) as client:
        print("🔍 Searching for channels and groups...")
        print("=" * 60)
        
        async for dialog in client.iter_dialogs():
            if isinstance(dialog.entity, (Channel, Chat)):
                entity = dialog.entity
                
                # Get the channel type
                if hasattr(entity, 'megagroup') and entity.megagroup:
                    channel_type = "Supergroup"
                elif hasattr(entity, 'broadcast') and entity.broadcast:
                    channel_type = "Channel"
                else:
                    channel_type = "Group"
                
                # Get the identifier
                if entity.username:
                    identifier = f"@{entity.username}"
                else:
                    # For channels without username, use the ID
                    identifier = f"-100{entity.id}"
                
                print(f"📢 {channel_type}: {entity.title}")
                print(f"   Username/ID: {identifier}")
                print(f"   Members: {getattr(entity, 'participants_count', 'Unknown')}")
                print(f"   Description: {getattr(entity, 'about', 'No description')[:100]}...")
                print("-" * 60)

if __name__ == "__main__":
    print("🚀 Telegram Channel Finder")
    print("This will show all channels and groups you have access to")
    print()
    
    try:
        asyncio.run(find_channels())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure your API credentials are correct in .env")
