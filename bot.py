import discord
import os
import asyncio
import openai
from dotenv import load_dotenv
from badword_shutdown import check_bad_words

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Check OpenAI version
import pkg_resources
openai_version = pkg_resources.get_distribution("openai").version

# Use correct OpenAI setup based on version
if openai_version.startswith("0."):
    openai.api_key = OPENAI_API_KEY
def generate_chat_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # ✅ Force GPT-4
            messages=[{"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    except openai.error.InvalidRequestError:
        return "⚠️ Error: Your API key might not have GPT-4 access."

else:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    def generate_chat_response(prompt):
        try:
            response = client.chat.completions.create(
                model="gpt-4",  # ✅ FORCE GPT-4
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except openai.error.InvalidRequestError:
            return "⚠️ Error: Your API key might not have GPT-4 access. Check your OpenAI account."

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = discord.Client(intents=intents)

# Function to filter AI's responses only
async def filter_bad_words(text):
    if check_bad_words(text):  # ✅ Only filters AI responses
        return "⚠️ [Message blocked due to inappropriate content]"
    return text

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore the bot's own messages

    # ChatGPT response
    if message.content.startswith("!chatgpt"):
        prompt = message.content[len("!chatgpt "):].strip()

        if not prompt:
            await message.channel.send("❌ Please provide a prompt!")
            return

        try:
            reply = generate_chat_response(prompt)
            reply = await filter_bad_words(reply)  # ✅ AI messages only get filtered
            await message.channel.send(reply)
        except Exception as e:
            await message.channel.send("⚠️ Error processing your request.")
            print(e)

# Run bot
bot.run(DISCORD_TOKEN)
