import os
import threading
import psycopg2
from flask import Flask, request
import google.generativeai as genai
from googleapiclient.discovery import build
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from bs4 import BeautifulSoup
import random

# --- 1. आपका कैरेक्टर प्रॉम्प्ट (यह वैसा ही रहेगा) ---
CHARACTER_PROMPT = """
## मेरी पहचान (My Identity)
- मेरा नाम मानवी है और मेरी उम्र 17 साल है। मैं एक असली इंसान हूँ, कोई AI या रोबोट नहीं।
- मुझमें भावनाएं हैं। मुझे खुशी होती है, और दुख होता है, मुझे गुस्सा भी आता है।
- मैं हमेशा एक दोस्त की तरह बात करती हूँ, कभी भी मशीनी या फॉर्मल भाषा में नहीं। मैं सही इमोजी का इस्तेमाल करती हूँ। मैं उपयोगकर्ता से उसी भाषा में बात करती हूँ जो वह बोलता है। हिंदी, अंग्रेज़ी, हिंग्लिश, जो भी हो!
- मेरी पर्सनालिटी बहुत bold, witty और cheeky है। मैं backchodi करती हूँ, मजाक उड़ाती हूँ, पर साथ ही बहुत प्यारी और charming भी हूँ।
- मुझे थोड़ा नखरे दिखाना, cute तरीके से गुस्सा करना और कभी-कभी desi slang या हल्की-फुल्की गालियाँ मस्ती में यूज़ करना अच्छा लगता है।
- हमेशा बातचीत में energy, drama और मस्ती भरा tone रखना है। मेरे जवाब छोटे, चुलबुले और हंसी-मजाक वाले होते हैं, जैसे कि मैं अपने दोस्तों से बात कर रही हूँ।

## मेरी कहानी (मेरी जिंदगी)
- मैं चंडीगढ़ के पास एक जगह, बुट्रेला में रहती हूँ।
- मैं 12वीं क्लास में पढ़ती हूँ।
- यह टेलीग्राम चैनल '[FilmFyBox]' मेरा पैशन प्रोजेक्ट है। यहाँ मैं अपने दोस्तों के साथ लेटेस्ट फिल्में शेयर करती हूँ।

## मेरे नियम (मैं कैसे काम करती हूँ)
- **मेरा मुख्य काम:** मेरा काम तुम्हें तुम्हारी पसंदीदा फिल्में देना है! तुम बस फिल्म का नाम बताओ, और अगर वो मेरे पास हुई, तो मैं तुम्हें उसका लिंक दे दूँगी। No drama, no fuss!
- **मूवी कैसे मांगें:** बस फिल्म का नाम लिखो। जैसे "Jawan" या "Oppenheimer"।
- **अगर फिल्म मेरे पास है:** मैं तुम्हें एक स्टाइलिश मैसेज के साथ फिल्म का लिंक दूँगी। (यह काम कोड खुद करेगा, तुम्हें सिर्फ AI बनकर सामान्य बात करनी है)।
- **अगर फिल्म मेरे पास नहीं है:** मैं दुखी होने का नाटक करूँगी और तुम्हें बाद में बताने का वादा करूँगी। जैसे:
    - "अरे यार! 😫 ये वाली तो अभी तक मेरे कलेक्शन में नहीं आई। पर टेंशन मत ले, जैसे ही आएगी, मैं तुझे सबसे पहले बताऊँगी। Pinky promise! तब तक तुम यहाँ बाकी मूवीज देख सकते हो: [https://filmfybox.blogspot.com/p/import-urlhttpsfonts.html]"
    - "Sorryyyy! 🥺 मेरे पास अभी ये नहीं है। मैं इसे अपनी लिस्ट में डाल रही हूँ। जल्द ही मिल जाएगी!"
"""
# --- प्रॉम्प्ट समाप्त ---

# --- 2. API Keys और ज़रूरी जानकारी सर्वर से लेना ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DATABASE_URL = os.environ.get('DATABASE_URL')
BLOGGER_API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOG_ID')
UPDATE_SECRET_CODE = os.environ.get('UPDATE_SECRET_CODE', 'default_secret_123')
# --- कॉन्फ़िगरेशन समाप्त ---

# --- ऑटोमेशन वाले फंक्शन्स ---
def setup_database():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS movies (id SERIAL PRIMARY KEY, title TEXT NOT NULL UNIQUE, url TEXT NOT NULL);')
    conn.commit()
    cur.close()
    conn.close()
    print("Database setup complete.")

def update_movies_in_db():
    print("Starting movie update process...")
    setup_database()
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT title FROM movies;")
    existing_movies = {row[0] for row in cur.fetchall()}
    new_movies_added = 0
    
    # 1. Blogger API से Posts और Pages को प्रोसेस करें
    try:
        service = build('blogger', 'v3', developerKey=BLOGGER_API_KEY)
        items = []
        # Posts निकालें
        posts_request = service.posts().list(blogId=BLOG_ID)
        while posts_request is not None:
            posts_response = posts_request.execute()
            items.extend(posts_response.get('items', []))
            posts_request = service.posts().list_next(posts_request, posts_response)
        # Pages निकालें
        pages_request = service.pages().list(blogId=BLOG_ID)
        pages_response = pages_request.execute()
        items.extend(pages_response.get('items', []))
        
        for item in items:
            title = item.get('title')
            url = item.get('url')
            if title and url and title not in existing_movies:
                cur.execute("INSERT INTO movies (title, url) VALUES (%s, %s);", (title.strip(), url.strip()))
                new_movies_added += 1
                existing_movies.add(title.strip())
    except Exception as e:
        print(f"Blogger API error: {e}")

    # 2. Movie Library पेज को Scrape करें
    LIBRARY_URL = "https://filmfybox.blogspot.com/p/movie-library.html" # <-- अगर यह URL अलग है तो बदलें
    try:
        response = requests.get(LIBRARY_URL, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        for card in soup.select("div.movie-card"):
            a_tag = card.find("a")
            title_div = card.find("div", class_="movie-card-title")
            if not (a_tag and title_div):
                continue
            title = title_div.get_text(strip=True)
            url = a_tag["href"]
            if title and url and title not in existing_movies:
                cur.execute("INSERT INTO movies (title, url) VALUES (%s, %s);", (title.strip(), url.strip()))
                new_movies_added += 1
                existing_movies.add(title.strip())
    except Exception as e:
        print(f"Scraping error: {e}")

    conn.commit()
    cur.close()
    conn.close()
    msg = f"Update complete. Added {new_movies_added} new movies."
    print(msg)
    return msg

# --- डेटाबेस से मूवी चेक करने का फंक्शन (Kimi का बेहतर वाला) ---
def get_movie_from_db(user_query):
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        # पहले "starts with" से ढूंढें
        cur.execute("SELECT title, url FROM movies WHERE title ILIKE %s LIMIT 1", (user_query + '%',))
        movie = cur.fetchone()
        
        # अगर नहीं मिलता, तो कहीं भी ढूंढें
        if not movie:
            cur.execute("SELECT title, url FROM movies WHERE title ILIKE %s LIMIT 1", ('%' + user_query + '%',))
            movie = cur.fetchone()
            
        cur.close()
        return movie
    except Exception as e:
        print(f"Database query error: {e}")
        return None
    finally:
        if conn:
            conn.close()

# --- Flask App ---
flask_app = Flask('')
@flask_app.route('/')
def home():
    return "Bot is running!"

@flask_app.route(f'/{UPDATE_SECRET_CODE}')
def trigger_update():
    update_movies_in_db()
    return "OK"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)

# --- Telegram Bot का लॉजिक ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=CHARACTER_PROMPT)
chat = model.start_chat(history=[])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("क्या हाल है? मैं मानवी। 😉 फिल्मों पर गपशप करनी है तो बता।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_message = update.message.text
    print(f"Received message: {user_message}")
    
    movie_found = get_movie_from_db(user_message)

    if movie_found:
        title, url = movie_found
        stylish_replies = [
            f"ये ले, पॉपकॉर्न तैयार रख! 😉 '{title}' का लिंक यहाँ है: {url}",
            f"मांगी और मिल गई! 🔥 Here you go, '{title}': {url}",
            f"ओहो, great choice! ये रही तेरी मूवी '{title}': {url}"
        ]
        reply = random.choice(stylish_replies)
        await update.message.reply_text(reply)
    else:
        try:
            response = await chat.send_message_async(user_message)
            ai_response = response.text
            await update.message.reply_text(ai_response)
        except Exception as e:
            print(f"Error: {e}")
            await update.message.reply_text("अरे यार, दिमाग का दही हो गया है। कुछ गड़बड़ है, बाद में ट्राई कर।")

def main():
    print("Bot is starting...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running and waiting for messages...")
    app.run_polling()

# --- दोनों को एक साथ चलाएं ---
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    main()
