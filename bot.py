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

# ✅ Support Message Variables
SUPPORT_MESSAGE = "💙 Love the bot? Help support premium features on [Patreon](https://www.patreon.com/c/user?u=80563219) 🚀"
SUPPORT_COMMAND_MESSAGE = "Want to unlock premium features? Support here: [Patreon](https://www.patreon.com/c/user?u=80563219) 🚀"

# ✅ Function to filter AI's responses only
async def filter_bad_words(text):
    if check_bad_words(text):
        return "⚠️ [Message blocked due to inappropriate content]"
    return text

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

    # ✅ Randomly Show Support Message (1 in 20 chance)
    if random.randint(1, 20) == 1:
        await message.channel.send(SUPPORT_MESSAGE)

    # ✅ Detect custom emojis
    if any(char.startswith("<:") and char.endswith(">") for char in message.content.split()):
        await message.channel.send("😃 I see you used a custom emoji! Looks cool! 🔥")
        return  # Stop further processing

    # ✅ Allow stickers in DMs and require !analyze in servers
    if message.stickers:
        if is_dm:
            for sticker in message.stickers:
                sticker_url = sticker.url  # Extract the sticker URL
                await message.channel.send("🔍 Processing sticker...")
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Describe the following sticker in detail."},
                            {"role": "user", "content": [
                                {"type": "image_url", "image_url": {"url": sticker_url}}
                            ]}
                        ]
                    ).choices[0].message.content
                    await message.channel.send(f"🎨 **Sticker Analysis:**\n{response}")
                except Exception as e:
                    print(f"⚠️ Error processing sticker: {e}")
                    await message.channel.send("⚠️ Sorry, I couldn't analyze the sticker. Try again later!")
        elif message.content.startswith("!analyze"):
            for sticker in message.stickers:
                sticker_url = sticker.url  # Extract the sticker URL
                await message.channel.send("🔍 Processing sticker...")
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Describe the following sticker in detail."},
                            {"role": "user", "content": [
                                {"type": "image_url", "image_url": {"url": sticker_url}}
                            ]}
                        ]
                    ).choices[0].message.content
                    await message.channel.send(f"🎨 **Sticker Analysis:**\n{response}")
                except Exception as e:
                    print(f"⚠️ Error processing sticker: {e}")
                    await message.channel.send("⚠️ Sorry, I couldn't analyze the sticker. Try again later!")
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
        conversation_history[user_id].append({"role": "user", "content": prompt})
        async with message.channel.typing():  # ✅ Show "typing..." before replying
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
