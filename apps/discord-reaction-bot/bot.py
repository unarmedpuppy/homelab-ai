"""
Tayne Discord Bot

An AI-powered Discord bot with absurdist/surreal humor inspired by the 
Tim & Eric "Celery Man" sketch. Responds when mentioned, maintains channel
conversation context, and has appropriate guardrails.

Features:
- LLM-powered responses via local-ai-router when @mentioned
- Channel-based conversation memory
- Rate limiting and spam protection
- Fallback quotes when guardrails trigger
- Random emoji reactions on non-mentions (33% chance)
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
    TAYNE_SYSTEM_PROMPT,
    FALLBACK_QUOTES,
    API_DOWN_MESSAGE,
    RATE_LIMITED_RESPONSES,
    TAYNE_REACTIONS,
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
LOCAL_AI_URL = os.environ.get('LOCAL_AI_URL', 'http://local-ai-router:8000')
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
    """
    Check if user is rate limited.
    
    Returns:
        (is_limited, is_rapid_fire): Tuple indicating if limited and if it's rapid fire spam
    """
    now = time.time()
    
    # Check basic cooldown
    if now - user_cooldowns[user_id] < COOLDOWN_SECONDS:
        return True, False
    
    # Check rapid-fire spam (many messages in short window)
    # Clean old timestamps
    user_message_times[user_id] = [
        t for t in user_message_times[user_id] 
        if now - t < RAPID_FIRE_WINDOW
    ]
    
    # Add current timestamp
    user_message_times[user_id].append(now)
    
    # Check if over threshold
    if len(user_message_times[user_id]) > RAPID_FIRE_THRESHOLD:
        return True, True
    
    # Update cooldown
    user_cooldowns[user_id] = now
    return False, False


def needs_fallback(response: str) -> bool:
    """
    Detect if the LLM response has gone off the rails or broken character.
    
    Returns:
        True if we should use a fallback quote instead
    """
    # Too long - Tayne should be concise
    if len(response) > DEFAULT_MAX_RESPONSE_LENGTH:
        return True
    
    # Check for character breaks (AI revealing itself)
    response_lower = response.lower()
    for phrase in CHARACTER_BREAK_PHRASES:
        if phrase in response_lower:
            return True
    
    return False


async def query_tayne(message: discord.Message) -> Optional[str]:
    """
    Query the local-ai-router with Tayne's persona.
    
    Args:
        message: The Discord message that mentioned Tayne
        
    Returns:
        Response text, or None if the API call failed
    """
    channel_id = str(message.channel.id)
    
    # Extract the actual message content, removing the mention
    user_message = message.content
    for mention in message.mentions:
        user_message = user_message.replace(f'<@{mention.id}>', '')
        user_message = user_message.replace(f'<@!{mention.id}>', '')
    user_message = user_message.strip()
    
    # If empty after removing mentions, use a default
    if not user_message:
        user_message = "Hello Tayne!"
    
    payload = {
        "model": "auto",
        "messages": [
            {"role": "system", "content": TAYNE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 200,
        "temperature": 0.9,
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Enable-Memory": "true",
        "X-Conversation-ID": f"discord-{channel_id}",
        "X-Project": "tayne-discord-bot",
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
                    
                    # Check guardrails
                    if needs_fallback(response_text):
                        print(f"Guardrail triggered, using fallback. Original: {response_text[:100]}...")
                        return random.choice(FALLBACK_QUOTES)
                    
                    return response_text
                else:
                    print(f"API returned status {resp.status}")
                    return None
    except asyncio.TimeoutError:
        print("API request timed out")
        return None
    except aiohttp.ClientError as e:
        print(f"API connection error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error querying API: {e}")
        return None


@client.event
async def on_ready():
    """Called when the bot successfully connects to Discord."""
    print(f'{client.user} has connected to Discord!')
    print(f'Tayne is ready. Now Tayne I can get into.')
    print(f'Connected to {len(client.guilds)} guild(s)')


@client.event
async def on_message(message: discord.Message):
    """Handle incoming Discord messages."""
    
    # Don't respond to our own messages
    if message.author == client.user:
        return
    
    # Check if Tayne was mentioned
    if client.user in message.mentions:
        await handle_mention(message)
        return
    
    # Non-mention: Maybe react with emoji (33% chance by default)
    if random.random() < REACTION_CHANCE:
        await add_random_reaction(message)


async def handle_mention(message: discord.Message):
    """Handle a message that mentions Tayne."""
    
    # Check rate limiting
    is_limited, is_rapid_fire = is_rate_limited(message.author.id)
    
    if is_limited:
        response = random.choice(RATE_LIMITED_RESPONSES)
        if is_rapid_fire:
            # Extra sass for spammers
            response = random.choice(FALLBACK_QUOTES)
        
        try:
            await message.channel.send(response)
        except discord.errors.Forbidden:
            print(f"Cannot send message in {message.channel}")
        return
    
    # Show typing indicator while we query the API
    async with message.channel.typing():
        response = await query_tayne(message)
    
    if response:
        try:
            await message.channel.send(response)
        except discord.errors.Forbidden:
            print(f"Cannot send message in {message.channel}")
    else:
        # API is down - send canned response
        try:
            await message.channel.send(API_DOWN_MESSAGE)
        except discord.errors.Forbidden:
            print(f"Cannot send message in {message.channel}")


async def add_random_reaction(message: discord.Message):
    """Add a random Tayne-appropriate emoji reaction to a message."""
    emoji = random.choice(TAYNE_REACTIONS)
    
    try:
        await message.add_reaction(emoji)
    except discord.errors.Forbidden:
        print(f"Cannot add reaction in {message.channel}")
    except discord.errors.HTTPException as e:
        # Handle unknown emoji or other issues
        print(f"Error adding reaction: {e}")
    except Exception as e:
        print(f"Unexpected error adding reaction: {e}")


# Run the bot
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
