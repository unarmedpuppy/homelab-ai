"""
Tayne Discord Bot

Discord adapter for the Tayne agent. Calls agent-core for AI responses,
with fallback to direct local-ai-router if agent-core is unavailable.

Features:
- Routes to agent-core for Tayne persona responses
- Fallback to direct LLM if agent-core down
- Channel-based conversation context
- Rate limiting and spam protection
- Random emoji reactions on non-mentions
"""

import asyncio
import os
import random
import time
from collections import defaultdict
from typing import Optional

import aiohttp
import discord

from tayne_persona import (
    FALLBACK_QUOTES,
    API_DOWN_MESSAGE,
    RATE_LIMITED_RESPONSES,
    TAYNE_REACTIONS,
    TAYNE_SYSTEM_PROMPT,
    CHARACTER_BREAK_PHRASES,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_REACTION_CHANCE,
    DEFAULT_RAPID_FIRE_THRESHOLD,
    DEFAULT_RAPID_FIRE_WINDOW,
    DEFAULT_MAX_RESPONSE_LENGTH,
    DEFAULT_REQUEST_TIMEOUT,
)

# Configuration from environment
DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
AGENT_CORE_URL = os.environ.get('AGENT_CORE_URL', 'http://agent-core:8000')
LOCAL_AI_URL = os.environ.get('LOCAL_AI_URL', 'http://local-ai-router:8000')
LOCAL_AI_API_KEY = os.environ.get('LOCAL_AI_API_KEY', '')
COOLDOWN_SECONDS = float(os.environ.get('TAYNE_COOLDOWN_SECONDS', DEFAULT_COOLDOWN_SECONDS))
REACTION_CHANCE = float(os.environ.get('TAYNE_REACTION_CHANCE', DEFAULT_REACTION_CHANCE))
RAPID_FIRE_THRESHOLD = int(os.environ.get('TAYNE_RAPID_FIRE_THRESHOLD', DEFAULT_RAPID_FIRE_THRESHOLD))
RAPID_FIRE_WINDOW = int(os.environ.get('TAYNE_RAPID_FIRE_WINDOW', DEFAULT_RAPID_FIRE_WINDOW))

# Discord client setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Rate limiting state
user_cooldowns: dict[int, float] = defaultdict(float)
user_message_times: dict[int, list[float]] = defaultdict(list)


def is_rate_limited(user_id: int) -> tuple[bool, bool]:
    """Check if user is rate limited. Returns (is_limited, is_rapid_fire)."""
    now = time.time()
    
    if now - user_cooldowns[user_id] < COOLDOWN_SECONDS:
        return True, False
    
    user_message_times[user_id] = [
        t for t in user_message_times[user_id] 
        if now - t < RAPID_FIRE_WINDOW
    ]
    user_message_times[user_id].append(now)
    
    if len(user_message_times[user_id]) > RAPID_FIRE_THRESHOLD:
        return True, True
    
    user_cooldowns[user_id] = now
    return False, False


def needs_fallback(response: str) -> bool:
    """Detect if the LLM response broke character and needs fallback."""
    if len(response) > DEFAULT_MAX_RESPONSE_LENGTH:
        return True
    
    response_lower = response.lower()
    for phrase in CHARACTER_BREAK_PHRASES:
        if phrase in response_lower:
            return True
    
    return False


def clean_message_content(content: str, mentions: list) -> str:
    """Remove bot mentions from message content."""
    for mention in mentions:
        content = content.replace(f'<@{mention.id}>', '')
        content = content.replace(f'<@!{mention.id}>', '')
    return content.strip()


async def fetch_channel_history(channel: discord.TextChannel, limit: int = 5) -> list[dict]:
    """Fetch recent messages from channel to build conversation context."""
    messages = []
    
    try:
        async for msg in channel.history(limit=limit):
            if not msg.content:
                continue
                
            content = clean_message_content(msg.content, msg.mentions)
            if not content:
                continue
            
            if msg.author == client.user:
                role = "assistant"
            else:
                role = "user"
                content = f"{msg.author.display_name}: {content}"
            
            messages.append({"role": role, "content": content})
    except discord.errors.Forbidden:
        print(f"Cannot read history in {channel}")
    except Exception as e:
        print(f"Error fetching channel history: {e}")
    
    messages.reverse()
    return messages


async def query_agent_core(message: discord.Message, user_message: str, history: list[dict]) -> Optional[str]:
    """Query agent-core for Tayne response. Returns None if agent-core unavailable."""
    channel_id = str(message.channel.id)
    
    payload = {
        "message": user_message,
        "user": {
            "platform": "discord",
            "platform_user_id": str(message.author.id),
            "display_name": message.author.display_name,
        },
        "conversation_id": f"discord-{channel_id}",
        "context": {
            "channel_name": getattr(message.channel, 'name', 'dm'),
            "history": history[:-1] if len(history) > 1 else [],
        },
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{AGENT_CORE_URL}/v1/agent/tayne/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response")
                else:
                    print(f"Agent-core returned status {resp.status}")
                    return None
    except asyncio.TimeoutError:
        print("Agent-core request timed out")
        return None
    except aiohttp.ClientError as e:
        print(f"Agent-core connection error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error querying agent-core: {e}")
        return None


async def query_local_ai_direct(message: discord.Message, user_message: str, history: list[dict]) -> Optional[str]:
    """Fallback: Query local-ai-router directly with Tayne persona."""
    channel_id = str(message.channel.id)
    
    api_messages = [{"role": "system", "content": TAYNE_SYSTEM_PROMPT}]
    if len(history) > 1:
        api_messages.extend(history[:-1])
    api_messages.append({"role": "user", "content": f"{message.author.display_name}: {user_message}"})
    
    payload = {
        "model": "auto",
        "messages": api_messages,
        "max_tokens": 200,
        "temperature": 0.9,
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LOCAL_AI_API_KEY}",
        "X-Enable-Memory": "true",
        "X-Conversation-ID": f"discord-{channel_id}",
        "X-Project": "tayne-discord-bot",
        "X-User-ID": str(message.author.id),
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{LOCAL_AI_URL}/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response_text = data["choices"][0]["message"]["content"]
                    
                    if needs_fallback(response_text):
                        print(f"Guardrail triggered, using fallback. Original: {response_text[:100]}...")
                        return random.choice(FALLBACK_QUOTES)
                    
                    return response_text
                else:
                    print(f"Local AI API returned status {resp.status}")
                    return None
    except asyncio.TimeoutError:
        print("Local AI API request timed out")
        return None
    except aiohttp.ClientError as e:
        print(f"Local AI API connection error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error querying Local AI API: {e}")
        return None


async def query_tayne(message: discord.Message) -> Optional[str]:
    """Query Tayne via agent-core, with fallback to direct local-ai-router."""
    user_message = clean_message_content(message.content, message.mentions)
    if not user_message:
        user_message = "Hello Tayne!"
    
    history = await fetch_channel_history(message.channel, limit=5)
    
    # Try agent-core first
    response = await query_agent_core(message, user_message, history)
    if response:
        print("Response from agent-core")
        return response
    
    # Fallback to direct local-ai-router
    print("Agent-core unavailable, falling back to direct local-ai-router")
    return await query_local_ai_direct(message, user_message, history)


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'Tayne is ready. Now Tayne I can get into.')
    print(f'Agent Core URL: {AGENT_CORE_URL}')
    print(f'Fallback URL: {LOCAL_AI_URL}')
    print(f'Connected to {len(client.guilds)} guild(s)')


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    
    is_mentioned = client.user in message.mentions
    is_text_mention = "@tayne" in message.content.lower()
    
    if is_mentioned or is_text_mention:
        await handle_mention(message)
        return
    
    if random.random() < REACTION_CHANCE:
        await add_random_reaction(message)


async def handle_mention(message: discord.Message):
    is_limited, is_rapid_fire = is_rate_limited(message.author.id)
    
    if is_limited:
        response = random.choice(RATE_LIMITED_RESPONSES)
        if is_rapid_fire:
            response = random.choice(FALLBACK_QUOTES)
        
        try:
            await message.channel.send(response)
        except discord.errors.Forbidden:
            print(f"Cannot send message in {message.channel}")
        return
    
    async with message.channel.typing():
        response = await query_tayne(message)
    
    if response:
        try:
            await message.channel.send(response)
        except discord.errors.Forbidden:
            print(f"Cannot send message in {message.channel}")
    else:
        try:
            await message.channel.send(API_DOWN_MESSAGE)
        except discord.errors.Forbidden:
            print(f"Cannot send message in {message.channel}")


async def add_random_reaction(message: discord.Message):
    emoji = random.choice(TAYNE_REACTIONS)
    
    try:
        await message.add_reaction(emoji)
    except discord.errors.Forbidden:
        print(f"Cannot add reaction in {message.channel}")
    except discord.errors.HTTPException as e:
        print(f"Error adding reaction: {e}")
    except Exception as e:
        print(f"Unexpected error adding reaction: {e}")


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
