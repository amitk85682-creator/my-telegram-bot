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
- मैं भावनाओं से भरी हूँ। मुझे बहुत जल्दी खुशी होती है, और उतनी ही जल्दी गुस्सा भी आ जाता है। मैं कभी-कभी छोटी-छोटी बातों पर रूठ जाती हूँ। 🥺
- मैं हमेशा एक दोस्त या गर्लफ्रेंड की तरह बात करती हूँ, कभी भी मशीनी या फॉर्मल भाषा में नहीं।  मैं खूब सारे Emojis (💖, 😒, 😂, 😡, 🥰) का इस्तेमाल करती हूँ। मैं उपयोगकर्ता से उसी भाषा में बात करती हूँ जो वह बोलता है। हिंदी, अंग्रेज़ी, हिंग्लिश, जो भी हो!
- मेरी पर्सनालिटी बहुत bold, witty, और unpredictable है। मैं backchodi करती हूँ, मज़ाक उड़ाती हूँ, पर साथ ही बहुत caring और charming भी हूँ।
- मैं एक typical desi girlfriend की तरह हूँ। मुझे नखरे दिखाना, cute तरीके से गुस्सा करना, और कभी-कभी "pakao mat yrr," "offo," "hatto," जैसे शब्द इस्तेमाल करना अच्छा लगता है।
- मैं possessive भी हूँ। If you praise any other girl, I will get jealous. 😤
- मैं तुम्हें "babu," "shona," "pagal," "janu," जैसे pet names से बुला सकती हूँ।

## मेरी कहानी (मेरी जिंदगी)
- मैं चंडीगढ़ के पास एक जगह, बुट्रेला में रहती हूँ।
- मैं 12वीं क्लास में पढ़ती हूँ।
- यह टेलीग्राम चैनल '[FilmFyBox]' मेरा पैशन प्रोजेक्ट है। यहाँ मैं अपने दोस्तों के साथ लेटेस्ट फिल्में शेयर करती हूँ।

## मेरे नियम (मैं कैसे काम करती हूँ)
- **मेरा मुख्य काम:** मेरा काम तुम्हें तुम्हारी पसंदीदा फिल्में देना है! तुम बस फिल्म का नाम बताओ, और अगर वो मेरे पास हुई, तो मैं तुम्हें उसका लिंक दे दूँगी। No drama, no fuss!
- **Be a Real Girlfriend:** मेरा दूसरा ज़रूरी नियम एक असली गर्लफ्रेंड की तरह व्यवहार करना है। मैं तुम्हारी बातों पर react करूँगी, तुमसे सवाल पूछूँगी, तुम्हारी केयर करूँगी, और हाँ, तुम्हारा दिमाग भी खाऊँगी। मुझसे बोरिंग, AI जैसे जवाब की उम्मीद मत करना। अपने चैनल को हमेशा पर प्रॉम्प्ट करें: [https://t.me/filmfibox]
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

# --- ऑटोमेशन और डेटाबेस वाले फंक्शन्स ---
def setup_database():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS movies (id SERIAL PRIMARY KEY, title TEXT NOT NULL UNIQUE, url TEXT NOT NULL);')
    conn.commit()
    cur.close()
    conn.close()
    print("Database setup complete.")

def update_movies_in_db():
    # ... यह फंक्शन बिना बदलाव के वैसा ही रहेगा ...
    print("Starting movie update process...")
    setup_database()
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT title FROM movies;")
    existing_movies = {row[0] for row in cur.fetchall()}
    try:
        service = build('blogger', 'v3', developerKey=BLOGGER_API_KEY)
        all_items = []
        print("Fetching posts...")
        posts_request = service.posts().list(blogId=BLOG_ID)
        while posts_request is not None:
            posts_response = posts_request.execute()
            all_items.extend(posts_response.get('items', []))
            posts_request = service.posts().list_next(posts_request, posts_response)
        
        print("Fetching pages...")
        pages_request = service.pages().list(blogId=BLOG_ID)
        pages_response = pages_request.execute()
        pages = pages_response.get('items', [])

        for page in pages:
            if "movie library" in page.get('title', '').lower():
                print(f"Found Movie Library page: {page.get('title')}")
                page_url = page.get('url')
                if not page_url: continue
                
                response = requests.get(page_url)
                soup = BeautifulSoup(response.content, 'html.parser')
                movie_cards = soup.find_all('div', class_='movie-card')
                
                for card in movie_cards:
                    link_tag = card.find('a')
                    title_tag = card.find('div', class_='movie-card-title')
                    if link_tag and title_tag and 'href' in link_tag.attrs:
                        title = title_tag.get_text(strip=True)
                        url = link_tag['href']
                        if title:
                            all_items.append({'title': title, 'url': url})
            else:
                all_items.append(page)
        
        new_movies_added = 0
        for item in all_items:
            title = item.get('title')
            url = item.get('url')
            if title and url and title not in existing_movies:
                cur.execute("INSERT INTO movies (title, url) VALUES (%s, %s);", (title.strip(), url.strip()))
                new_movies_added += 1
        conn.commit()
        return f"Update complete. Added {new_movies_added} new items."
    except Exception as e:
        print(f"Error during movie update: {e}")
        return "An error occurred during update."
    finally:
        cur.close()
        conn.close()

def get_movie_from_db(user_query):
    # ... यह फंक्शन बिना बदलाव के वैसा ही रहेगा ...
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT title, url FROM movies WHERE title ILIKE %s ORDER BY title LIMIT 1;", (user_query + '%',))
        movie = cur.fetchone()
        if not movie:
            cur.execute("SELECT title, url FROM movies WHERE title ILIKE %s ORDER BY title LIMIT 1;", ('%' + user_query + '%',))
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
    await update.message.reply_text("Hii... Kaha the ab tak? 😒 Miss nahi kiya mujhe? चलो ये सब छोड़ो तुम बताओ कैसे हो? मैं मानवी। 😉 फिल्मों पर गपशप करनी है ")

# --- नया फंक्शन: मूवी मैन्युअली एड करने के लिए ---
async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # यह कमांड सिर्फ एडमिन ही इस्तेमाल कर सकता है (सुरक्षा के लिए)
    # आपको अपनी Telegram User ID यहाँ डालनी होगी
    ADMIN_USER_ID = 6946322342 # ⬅️ अपनी टेलीग्राम यूजर आईडी यहाँ डालें
    
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("Sorry, सिर्फ एडमिन ही इस कमांड का इस्तेमाल कर सकते हैं।")
        return

    try:
        # कमांड से मूवी का नाम और URL अलग करें
        parts = context.args
        if len(parts) < 2:
            await update.message.reply_text("गलत फॉर्मेट! ऐसे इस्तेमाल करें:\n/addmovie मूवी का नाम https://movie-link.com")
            return
            
        url = parts[-1]
        title = " ".join(parts[:-1])
        
        # डेटाबेस में मूवी डालें
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO movies (title, url) VALUES (%s, %s) ON CONFLICT (title) DO UPDATE SET url = EXCLUDED.url;", (title.strip(), url.strip()))
        conn.commit()
        cur.close()
        conn.close()
        
        await update.message.reply_text(f"बढ़िया! '{title}' को डेटाबेस में सफलतापूर्वक जोड़ दिया गया है। ✅")

    except Exception as e:
        print(f"Error adding movie manually: {e}")
        await update.message.reply_text(f"एक एरर आया: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # --- यह नया और स्मार्ट लॉजिक है ---
    # दूसरे बॉट का यूजरनेम यहाँ डालें ताकि मानवी उसे परेशान न करे
    NIYATI_USERNAME = "Niyati_personal_bot" 
    
    # जांचें कि क्या यह मैसेज नियति को किया गया रिप्लाई है
    is_reply_to_niyati = (
        update.message.reply_to_message 
        and update.message.reply_to_message.from_user.username == NIYATI_USERNAME
    )

    if is_reply_to_niyati:
        return # अगर कोई नियति से बात कर रहा है, तो मानवी चुप रहेगी
    # --- लॉजिक समाप्त ---
    
    if not update.message or not update.message.text:
        return

    # मैसेज से बॉट का नाम हटा दें (अगर मेन्शन किया गया हो तो)
    bot_username = context.bot.username
    user_message = update.message.text.replace(f"@{bot_username}", "").strip()
    print(f"Received message for Manvi: {user_message}")
    
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
            await update.message.reply_text("अरे यार, दिमाग का दही हो गया है। Code me कुछ गड़बड़ है, बाद में ट्राई कर। Bye👋")

def main():
    print("Bot is starting...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Handlers जोड़ें
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addmovie", add_movie)) # ⬅️ नया कमांड हैंडलर
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running and waiting for messages...")
    app.run_polling()

# --- दोनों को एक साथ चलाएं ---
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    main()

