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
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")  # ✅ Web Search API Key

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

async def search_web(query):
    """Fetch live search results from the web."""
    search_url = f"https://api.searchengine.com/search?q={query}&api_key={SEARCH_API_KEY}"
    try:
        response = requests.get(search_url)
        data = response.json()
        
        if "results" in data and len(data["results"]) > 0:
            top_result = data["results"][0]
            title = top_result["title"]
            url = top_result["url"]
            snippet = top_result.get("snippet", "No description available.")
            return f"🔍 **Latest Search Result:**\n**{title}**\n{snippet}\n🔗 [Read more]({url})"
        else:
            return "❌ No relevant search results found."
    except Exception as e:
        print(f"⚠️ Web Search Error: {e}")
        return "⚠️ Error fetching search results."

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="@mentions | !chatgpt"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore the bot's own messages

    is_dm = isinstance(message.channel, discord.DMChannel)
    prompt = message.content.lower()

    # ✅ Handle Web Search Queries
    if "look it up" in prompt or "search for" in prompt:
        query = prompt.replace("look it up", "").replace("search for", "").strip()
        if not query:
            await message.channel.send("❌ Please specify what I should search for!")
            return
        
        await message.channel.send("🔍 Searching the web... Please wait.")
        search_result = await search_web(query)
        await message.channel.send(search_result)
        return

    # ✅ Handle stickers as images
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

    # ✅ Handle Tenor/Giphy GIF links
    if "tenor.com" in message.content or "giphy.com" in message.content:
        await message.channel.send("🎥 Looks like you sent a GIF! Unfortunately, I can't process GIFs directly, but I can still chat about it! Tell me what's happening in the GIF! 😊")
        return

    # ✅ Respond when mentioned (@ChatGPT)
    if bot.user in message.mentions:
        response = await chat_with_ai(message, message.content)
        await message.channel.send(response)

    # ✅ Handle ChatGPT responses in DMs or when using "!chatgpt"
    if is_dm or message.content.startswith("!chatgpt"):
        response = await chat_with_ai(message, message.content)
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
