import discord
import os
import openai
import aiohttp
import random
import requests
import asyncio
from dotenv import load_dotenv
from badword_shutdown import check_bad_words
import keep_alive  # ✅ Keep bot online

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Set OpenAI API key
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ✅ Start web server (for Railway hosting)
keep_alive.keep_alive()

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = discord.Client(intents=intents)

# ✅ Dictionary to store user-specific names in DMs
user_custom_names = {}
conversation_history = {}
cooldowns = {}

# ✅ Support Message Variables
SUPPORT_MESSAGE = "💙 Love the bot? Help support premium features on [Patreon](https://www.patreon.com/user?u=80563219) 🚀"
SUPPORT_COMMAND_MESSAGE = "Want to unlock premium features? Support here: [Patreon](https://www.patreon.com/user?u=80563219) 🚀"

# ✅ Function to filter AI's responses only
async def filter_bad_words(text):
    if check_bad_words(text):
        return "⚠️ [Message blocked due to inappropriate content]"
    return text

# ✅ Categorize emojis for better responses
emoji_responses = {
    "happy": ["😃", "😄", "😁", "😊", "🙂", "😆"],
    "sad": ["😢", "😭", "🥺", "😞", "😔"],
    "angry": ["😠", "😡", "🤬"],
    "funny": ["🤣", "😂", "😆", "😹"],
    "cool": ["😎", "🔥", "💯"],
    "awkward": ["🫠", "😬", "😳"],
    "pepe": ["🐸", "🫂", "Sadge", "PepeHands"],
}

async def get_emoji_response(emoji):
    for category, emojis in emoji_responses.items():
        if emoji in emojis:
            if category == "happy":
                return random.choice(["You're spreading some good vibes! 😊", "Love the positivity! 😃"])
            if category == "sad":
                return random.choice(["Oh no, everything okay? 🥺", "Sending virtual hugs! 🤗"])
            if category == "angry":
                return random.choice(["Whoa, what's got you fired up? 😠", "Take a deep breath! 💨"])
            if category == "funny":
                return random.choice(["Haha, that's a good one! 🤣", "You got jokes! 😂"])
            if category == "cool":
                return random.choice(["Looking sharp! 😎🔥", "Absolute legend! 💯"])
            if category == "awkward":
                return random.choice(["Oof, that moment... 🫠", "I feel that too. 😬"])
            if category == "pepe":
                return random.choice(["Sadge... 🥺", "PepeHands... 💔"])
    return "Nice emoji! 👍"

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="@mentions | !chatgpt | !analyze | !support"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore the bot's own messages

    is_dm = isinstance(message.channel, discord.DMChannel)
    prompt = message.content.lower()
    user_id = message.author.id

    # ✅ Enforce Rate Limits (5-second cooldown per user)
    if user_id in cooldowns and cooldowns[user_id] > asyncio.get_event_loop().time():
        await message.channel.send("⏳ Please wait a few seconds before using the bot again.")
        return
    cooldowns[user_id] = asyncio.get_event_loop().time() + 5  # Set 5-second cooldown

    # ✅ Randomly Show Support Message (1 in 20 chance)
    if random.randint(1, 20) == 1:
        await message.channel.send(SUPPORT_MESSAGE)

    # ✅ Detect and respond to emojis
    for char in message.content:
        response = await get_emoji_response(char)
        if response:
            await message.channel.send(response)
            return  # Stop further processing

    # ✅ Support Command
    if message.content.startswith("!support"):
        await message.channel.send(SUPPORT_COMMAND_MESSAGE)
        return

    # ✅ Respond naturally to @mentions
    if bot.user in message.mentions:
        response = await chat_with_ai(message, message.content)
        if not response.strip():
            response = "Hey there! Need something? 😊"
        await message.channel.send(response)

    # ✅ Handle ChatGPT responses in DMs or when using "!chatgpt"
    if is_dm or message.content.startswith("!chatgpt"):
        response = await chat_with_ai(message, message.content)
        if not response.strip():
            response = "I'm here! What’s up? 🤖"
        await message.channel.send(response)

async def chat_with_ai(message, prompt):
    """Helper function to handle AI chat responses with a typing effect and memory."""
    try:
        user_id = message.author.id
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        conversation_history[user_id] = conversation_history[user_id][-10:]  # Keep last 10 messages
        conversation_history[user_id].append({"role": "user", "content": prompt})
        async with message.channel.typing():
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=conversation_history[user_id]
            ).choices[0].message.content
            response = await filter_bad_words(response)
            conversation_history[user_id].append({"role": "assistant", "content": response})
            bot_name = user_custom_names.get(message.author.id, "ChatGPT")
            return response.replace("ChatGPT", bot_name)
    except Exception as e:
        print(f"⚠️ Error processing request: {e}")
        return "⚠️ Error processing your request."

# ✅ Run bot
bot.run(DISCORD_TOKEN)
