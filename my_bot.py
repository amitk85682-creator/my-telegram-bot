import os
import threading
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. आपका सुधारा हुआ कैरेक्टर प्रॉम्प्ट ---
CHARACTER_PROMPT = """Hello, I am a test bot. I am working correctly."""
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





