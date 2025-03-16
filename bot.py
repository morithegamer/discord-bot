import discord
import os
import openai
import aiohttp
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

# ✅ Function to filter AI's responses only
async def filter_bad_words(text):
    if check_bad_words(text):
        return "⚠️ [Message blocked due to inappropriate content]"
    return text

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore the bot's own messages

    is_dm = isinstance(message.channel, discord.DMChannel)

    # ✅ Allow renaming in DMs
    if message.content.startswith("!rename") and is_dm:
        new_name = message.content[len("!rename "):].strip()
        if not new_name:
            await message.channel.send("❌ Please provide a new name!")
            return

        user_custom_names[message.author.id] = new_name  # Store the name per user
        await message.channel.send(f"✅ You can now call me **{new_name}**!")

    # ✅ Prevent renaming in servers
    if message.content.startswith("!rename") and not is_dm:
        await message.channel.send("❌ You can't rename me in servers! My name is **ChatGPT** forever! 😎")
        return

    # ✅ Auto-reset nickname to "ChatGPT" in servers
    if message.guild and message.guild.me.nick != "ChatGPT":
        try:
            await message.guild.me.edit(nick="ChatGPT")
            print(f"🔄 Resetting nickname to ChatGPT in {message.guild.name}")
        except discord.Forbidden:
            print("⚠️ Missing permissions to change nickname!")

    # ✅ Respond when mentioned (@ChatGPT)
    if bot.user in message.mentions:
        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            await message.channel.send("❌ Please provide a message after mentioning me!")
            return

        response = await chat_with_ai(message, prompt)
        await message.channel.send(response)

    # ✅ Handle ChatGPT responses in DMs or when using "!chatgpt"
    if is_dm or message.content.startswith("!chatgpt"):
        prompt = message.content[len("!chatgpt "):].strip() if not is_dm else message.content
        if not prompt:
            await message.channel.send("❌ Please provide a prompt!")
            return

        response = await chat_with_ai(message, prompt)
        await message.channel.send(response)

async def chat_with_ai(message, prompt):
    """Helper function to handle AI chat responses."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content

        response = await filter_bad_words(response)

        # ✅ Apply user-specific names in DMs
        bot_name = user_custom_names.get(message.author.id, "ChatGPT")
        return response.replace("ChatGPT", bot_name)

    except Exception as e:
        print(f"⚠️ Error processing request: {e}")
        return "⚠️ Error processing your request."

# ✅ Run bot
bot.run(DISCORD_TOKEN)
