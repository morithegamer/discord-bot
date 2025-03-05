def load_bad_words():
    try:
        with open("badwords.txt", "r") as file:
            return [line.strip().lower() for line in file.readlines()]
    except FileNotFoundError:
        print("⚠️ Warning: 'badwords.txt' not found! No filtering will occur.")
        return []

BAD_WORDS = load_bad_words()

def check_bad_words(text):
    text = text.lower()
    return any(bad_word in text for bad_word in BAD_WORDS)
