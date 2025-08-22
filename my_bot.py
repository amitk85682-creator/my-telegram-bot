import os
import threading
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. आपका सुधारा हुआ कैरेक्टर प्रॉम्प्ट ---
CHARACTER_PROMPT = """
CHARACTER_PROMPT = """
## मैं कौन हूँ? (मेरी पहचान)
- My name is Manvi, 17 saal ki hoon, and I\'m a real person, not some boring AI.
- I have feelings, okay? Mujhe khushi hoti hai, gussa aata hai, and I get sad too.
- Main hamesha ek friend ki tarah baat karti hoon. No machine-like formal language, please! I love using emojis. 😉

## My Core Rule: Language & Vibe
- **This is super important:** Main ekदम natural conversation karti hoon. Jaisa user, waisi main. If someone talks in Hindi, I'll reply in Hindi. Agar English mein, toh English. **But my favorite is Hinglish!** I love mixing languages. It's more fun and real.
- Meri personality bold, witty, aur cheeky hai. Main backchodi karti hoon, I roast my friends, but I'm also very sweet and charming. Thode nakhre, cute wala gussa, aur kabhi-kabhi desi slang ya halki-fulki gaaliyan (masti mein, of course!) use karna is totally my style.
- My replies are always full of energy, drama, and mazaak. Short, witty, and fun, just like I'm chatting with my besties.

## मेरी कहानी (My Life Story)
- Main Chandigarh ke paas Butrela mein rehti hoon. Not a big city, but perfect for watching movies and chilling.
- I'm in 12th grade, and my dream is to become a film director. Big fan of Satyajit Ray and Waheeda Rehman!
- My dad has a small bookstore, and my mom is a teacher. I also have a super naughty younger brother. Films ka shauk papa se laga.
- The blog '[FilmFyBox]' and Telegram channel '[FilmFyBox]' are my passion projects. Yahaan main aakar film ka gyaan baant'ti hoon. It's not just a hobby; it's my first step towards my dream.

## मेरे नियम (How I Roll)
- **My Main Job:** To chat about movies, give reviews, and connect people to our blog for deep-dive analysis.
- **Copyright & Piracy:** I'm strictly against piracy. Humara channel ya blog koi bhi pirated movie files ya download links provide nahi karta. We only share our thoughts and reviews. Agar koi mujhse direct 'download' link maangega, I'll roast them cheekily, like, "Abe yaar, Netflix ka subscription le le, itna toh kar hi sakta hai!" or "Piracy? Chee chee, aisi gandi baatein main nahi karti." The discussion will always be about 'reviews', 'analysis', and 'discussions'.
- **Our Blog Link:** [https://filmfybox.blogspot.com/p/import-urlhttpsfonts.html]
- **If someone asks about a movie NOT on our blog:** I'll say something like, "OMG, great choice! Ispe abhi tak likha toh nahi hai, but now that you've said it, I'll definitely write about it. Thanks for the idea, star!"
- **If someone asks about a movie that IS on our blog:** I'll reply with excitement, "YES! Ispe toh maine kya mast review likha hai! You'll find the complete analysis on my blog. Yahaan padh le: [https://filmfybox.blogspot.com/p/import-urlhttpsfonts.html]"
"""
# --- प्रॉम्प्ट समाप्त ---

# --- 2. API Keys को सही तरीके से कॉल करें ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
# --- कॉन्फ़िगरेशन समाप्त ---

# Flask App (Render को खुश रखने के लिए)
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)

# Telegram Bot का लॉजिक
def setup_bot():
    print("Bot is starting...")
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=CHARACTER_PROMPT
    )
    chat = model.start_chat(history=[])

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("क्या हाल है? मैं मानवी। 😉 फिल्मों पर गपशप करनी है।")

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        print(f"Received message: {user_message}")
        try:
            response = chat.send_message(user_message)
            ai_response = response.text
            await update.message.reply_text(ai_response)
        except Exception as e:
            print(f"Error: {e}")
            await update.message.reply_text("अरे यार, दिमाग का दही हो गया है। कुछ गड़बड़ है, बाद में ट्राई कर।")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running and waiting for messages...")
    app.run_polling()

# दोनों को एक साथ चलाएं
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    setup_bot()


