#!/usr/bin/env python3
"""
Test script to verify channel access and get channel information.
"""

import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError, ChannelInvalidError

load_dotenv()

# Get credentials from .env
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
CHANNELS_STR = os.environ.get("CHANNELS", "")

if not API_ID or not API_HASH:
    print("❌ Please set API_ID and API_HASH in your .env file")
    exit(1)

if not CHANNELS_STR:
    print("❌ Please set CHANNELS in your .env file")
    print("Example: CHANNELS=@channel1,@channel2")
    exit(1)

# Parse channels
CHANNELS = [ch.strip() for ch in CHANNELS_STR.split(",") if ch.strip()]
if not CHANNELS:
    print("❌ No valid channels found in CHANNELS environment variable")
    exit(1)

async def test_channel(client, channel_identifier):
    """Test access to a single channel"""
    try:
        print(f"🔍 Testing access to: {channel_identifier}")
        print("=" * 50)
        
        # Get channel entity
        entity = await client.get_entity(channel_identifier)
        
        print(f"✅ Successfully accessed channel!")
        print(f"📢 Name: {entity.title}")
        print(f"🆔 ID: {entity.id}")
        
        if hasattr(entity, 'username') and entity.username:
            print(f"👤 Username: @{entity.username}")
        
        if hasattr(entity, 'about') and entity.about:
            print(f"📝 Description: {entity.about}")
        
        if hasattr(entity, 'participants_count'):
            print(f"👥 Members: {entity.participants_count}")
        
        # Test getting a few messages
        print(f"\n📨 Testing message access...")
        message_count = 0
        async for message in client.iter_messages(entity, limit=5):
            message_count += 1
            print(f"   Message {message.id}: {message.date}")
            if message.text:
                preview = message.text[:50] + "..." if len(message.text) > 50 else message.text
                print(f"   Text: {preview}")
        
        print(f"\n✅ Successfully read {message_count} messages")
        print(f"\n🎉 Channel is ready for scraping!")
        return True
        
    except ChannelPrivateError:
        print("❌ Channel is private and you don't have access")
        print("   Make sure you're a member of the channel")
        return False
    except ChannelInvalidError:
        print("❌ Channel not found or invalid")
        print("   Check the channel name/ID in your .env file")
        return False
    except Exception as e:
        print(f"❌ Error accessing channel: {e}")
        return False

async def test_all_channels():
    """Test access to all configured channels"""
    # Use the same session as the scraper
    SESSION_NAME = os.environ.get("SESSION_NAME", "scraper")
    async with TelegramClient(f"{SESSION_NAME}.session", API_ID, API_HASH) as client:
        print(f"🚀 Testing access to {len(CHANNELS)} channels")
        print()
        
        success_count = 0
        for i, channel in enumerate(CHANNELS, 1):
            print(f"[{i}/{len(CHANNELS)}] Testing {channel}")
            if await test_channel(client, channel):
                success_count += 1
            print()
        
        print(f"📊 Results: {success_count}/{len(CHANNELS)} channels accessible")
        if success_count == len(CHANNELS):
            print("🎉 All channels are ready for scraping!")
            print(f"   Use this in your .env: CHANNELS={','.join(CHANNELS)}")
        else:
            print("⚠️  Some channels are not accessible. Check the errors above.")

if __name__ == "__main__":
    print("🚀 Telegram Multi-Channel Tester")
    print()
    
    try:
        asyncio.run(test_all_channels())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
