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

    # ✅ Handle multiple image uploads for OCR + Image Description
    if message.attachments:
        results = []  # List to store results for each image

        for attachment in message.attachments:
            if attachment.content_type and "image" in attachment.content_type:
                await message.channel.send("🔍 Processing image...")

                # Download the image
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status != 200:
                            await message.channel.send("❌ Failed to download image.")
                            return
                        image_bytes = await resp.read()

                # Send image to OpenAI Vision API
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Extract any visible text from this image. If no text is found, describe the image instead."},
                            {"role": "user", "content": [
                                {"type": "text", "text": "Analyze this image and extract text if available. If no text is found, provide a short description of the image:"},
                                {"type": "image_url", "image_url": attachment.url}
                            ]}
                        ],
                        max_tokens=500
                    )

                    extracted_text = response.choices[0].message.content.strip()

                    # ✅ Log the OCR result for debugging
                    print(f"📜 [OCR Result] Image URL: {attachment.url}\nExtracted Text:\n{extracted_text}\n")

                    # ✅ Store the result for later sending
                    results.append(f"📜 **Extracted Text / Description (Image {len(results)+1}):**\n```{extracted_text}```")

                except Exception as e:
                    print(f"⚠️ Error processing image: {e}")
                    results.append(f"❌ Error processing image {len(results)+1}.")

        # ✅ Send results as a single message (DM or Channel)
        if results:
            final_result = "\n\n".join(results)

            try:
                # Try to send a DM
                await message.author.send(final_result)
                await message.channel.send("📩 **Results sent via DM!**")
            except discord.Forbidden:
                # If user has DMs disabled, send in the channel
                await message.channel.send(final_result)

    # ✅ Handle ChatGPT text responses
    if message.content.startswith("!chatgpt"):
        prompt = message.content[len("!chatgpt "):].strip()

        if not prompt:
            await message.channel.send("❌ Please provide a prompt!")
            return

        try:
            reply = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content

            reply = await filter_bad_words(reply)
            await message.channel.send(reply)
        except Exception as e:
            await message.channel.send("⚠️ Error processing your request.")
            print(e)

# ✅ Run bot
bot.run(DISCORD_TOKEN)
