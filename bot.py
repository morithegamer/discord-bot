import discord
import os
import openai
import aiohttp
import random
import requests
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

# ✅ Function to filter AI's responses only
async def filter_bad_words(text):
    if check_bad_words(text):
        return "⚠️ [Message blocked due to inappropriate content]"
    return text

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="@mentions | !chatgpt | !analyze"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore the bot's own messages

    is_dm = isinstance(message.channel, discord.DMChannel)
    prompt = message.content.lower()

    # ✅ Handle sticker analysis (Require Command)
    if message.stickers and message.content.startswith("!analyze"):
        for sticker in message.stickers:
            sticker_url = sticker.url  # Extract the sticker URL
            await message.channel.send("🔍 Processing sticker...")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Describe this sticker in detail."},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": sticker_url}}
                    ]}
                ]
            ).choices[0].message.content
            await message.channel.send(f"🎨 **Sticker Analysis:**\n{response}")
            return  # Stop further processing

    # ✅ Handle image attachments properly (Require Command)
    if message.attachments and message.content.startswith("!analyze"):
        for attachment in message.attachments:
            if "image" in attachment.content_type:
                await message.channel.send("🔍 Processing image...")
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Describe this image or extract text if available."},
                        {"role": "user", "content": [
                            {"type": "image_url", "image_url": {"url": attachment.url}}
                        ]}
                    ]
                ).choices[0].message.content
                await message.channel.send(f"📜 **Image Analysis:**\n{response}")
                return  # Stop further processing

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
        conversation_history[user_id].append({"role": "user", "content": prompt})
        async with message.channel.typing():  # ✅ Show "typing..." before replying
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=conversation_history[user_id]
            ).choices[0].message.content
            response = await filter_bad_words(response)
            conversation_history[user_id].append({"role": "assistant", "content": response})
            bot_name = user_custom_names.get(message.author.id, "ChatGPT")

            # ✅ Make responses feel more natural like Clyde
            if prompt.lower() in ["hi", "hello", "hey", "yo", "sup"]:
                return random.choice([
                    f"Hey {message.author.name}! 😊",
                    "Hello there! Need anything? 😃",
                    "Yo! How’s your day going? 🔥",
                    "Hey hey! What's up? 🤖"
                ])
            if prompt.lower() in ["nothing", "just chilling", "idk"]:
                return random.choice([
                    "Fair enough, just vibing here too. ☁️",
                    "That’s valid. Sometimes it’s nice to just exist. 🌿",
                    "No worries! If you need anything, just ask! 😊"
                ])
            return response.replace("ChatGPT", bot_name)
    except Exception as e:
        print(f"⚠️ Error processing request: {e}")
        return "⚠️ Error processing your request."

# ✅ Run bot
bot.run(DISCORD_TOKEN)
