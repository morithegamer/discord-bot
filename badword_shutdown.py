import re  # Import regex module

# Load bad words from the badwords.txt file
def load_bad_words():
    try:
        with open("badwords.txt", "r", encoding="utf-8") as file:
            return [line.strip().lower() for line in file if line.strip()]
    except FileNotFoundError:
        print("⚠️ Warning: badwords.txt not found! No filtering will be applied.")
        return []

BAD_WORDS = load_bad_words()

# Function to check messages for bad words
def check_bad_words(text):
    text = text.lower()
    for bad_word in BAD_WORDS:
        if re.search(rf"\b{re.escape(bad_word)}\b", text):  # Match full words only
            print(f"🚨 Blocked word found: {bad_word}")  # Debugging print
            return True
    return False
