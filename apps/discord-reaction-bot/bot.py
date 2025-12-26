import discord
import os
import random

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Reactions to use (randomly picks one)
REACTIONS = [
    '🍆',  # eggplant
    '🫡',  # salute
    '🍤',  # shrimp
    '💩',  # poop
    '🤡',  # clown
    '🚀',  # rocket
    '👌',  # ok hand
    '🤌',  # pinched fingers
]

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    # Don't react to our own messages
    if message.author == client.user:
        return

    # Don't react to bot messages (unless they mention us)
    if message.author.bot:
        if client.user not in message.mentions:
            return
        # Use robot emoji for bot/webhook mentions
        emoji = '🤖'
    else:
        # Use random emoji for human messages
        emoji = random.choice(REACTIONS)

    # Add reaction
    try:
        await message.add_reaction(emoji)
    except discord.errors.Forbidden:
        print(f"Cannot add reaction in {message.channel}")
    except Exception as e:
        print(f"Error adding reaction: {e}")

client.run(os.environ['DISCORD_TOKEN'])
