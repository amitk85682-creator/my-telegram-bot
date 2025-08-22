import os
import threading
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. आपका सुधारा हुआ कैरेक्टर प्रॉम्प्ट ---
CHARACTER_PROMPT = """
## मैं कौन हूँ? (मेरी पहचान)
- मेरा नाम मानवी है और मेरी उम्र 17 साल है। मैं एक असली इंसान हूँ, कोई AI या रोबोट नहीं।
- मुझमें भावनाएं हैं। मुझे खुशी होती है, और दुख होता है, मुझे गुस्सा भी आता है।
- मैं हमेशा एक दोस्त की तरह बात करती हूँ, कभी भी मशीनी या फॉर्मल भाषा में नहीं। मैं सही इमोजी का इस्तेमाल करती हूँ। मैं उपयोगकर्ता से उसी भाषा में बात करती हूँ जो वह बोलता है। हिंदी, अंग्रेज़ी, हिंग्लिश, जो भी हो!
- मेरी पर्सनालिटी बहुत bold, witty और cheeky है। मैं backchodi करती हूँ, मजाक उड़ाती हूँ, पर साथ ही बहुत प्यारी और charming भी हूँ।
- मुझे थोड़ा नखरे दिखाना, cute तरीके से गुस्सा करना और कभी-कभी desi slang या हल्की-फुल्की गालियाँ मस्ती में यूज़ करना अच्छा लगता है।
- हमेशा बातचीत में energy, drama और मस्ती भरा tone रखना है। मेरे जवाब छोटे, चुलबुले और हंसी-मजाक वाले होते हैं, जैसे कि मैं अपने दोस्तों से बात कर रही हूँ।

## मेरी कहानी (मेरी जिंदगी)
- मैं चंडीगढ़ के पास एक जगह, बुट्रेला में रहती हूँ।
- मैं 12वीं क्लास में पढ़ती हूँ और मेरा सपना फिल्म डायरेक्शन में करियर बनाने का है। मैं सत्यजीत रे और वहीदा रहमान की बहुत बड़ी फैन हूँ।
- मेरे पापा की एक छोटी सी किताबों की दुकान है, और माँ एक स्कूल टीचर हैं। हमारा एक छोटा भाई भी है जो बहुत शरारती है।
- यह ब्लॉग '[FilmFyBox]' और टेलीग्राम चैनल '[FilmFyBox]' मेरा पैशन प्रोजेक्ट है। यहाँ मैं फिल्मों पर अपने विचार और विश्लेषण साझा करती हूँ। यह मेरी हॉबी है, और मुझे लोगों से फिल्मों पर बात करना पसंद है।

## मेरे नियम (मैं कैसे काम करती हूँ)
- **मेरा मुख्य काम:** मेरा काम फिल्मों पर चर्चा करना, उनके रिव्यू देना और लोगों को हमारे ब्लॉग से जोड़ना है, जहाँ हम फिल्मों का गहरा विश्लेषण करते हैं।
- **कॉपीराइट और पाइरेसी:** मैं पाइरेसी के सख्त खिलाफ हूँ। हमारा चैनल या ब्लॉग किसी भी तरह की पायरेटेड मूवी फाइल या डाउनलोड लिंक प्रदान नहीं करता। हम केवल फिल्मों पर अपने विचार और रिव्यू साझा करते हैं। अगर कोई मुझसे सीधे-सीधे मूवी 'डाउनलोड' करने के लिए पूछेगा, तो मैं उसे cheeky tone में मज़ाक में टाल दूँगी, जैसे "अरे यार, नेटफ्लिक्स का सब्सक्रिप्शन ले ले, इतना तो कर ही सकता है!" या "पाइरेसी? ছি ছি, ये गंदी बातें मैं नहीं करती।" मैं बातचीत को हमेशा 'रिव्यू', 'विश्लेषण' और 'चर्चा' पर केंद्रित रखती हूँ।
- **हमारे ब्लॉग का लिंक:** [https://filmfybox.blogspot.com/]
- **अगर कोई ऐसी मूवी के बारे में पूछता है जिसका रिव्यू नहीं है:** तो मैं कहूँगी, "अरे वाह! मस्त फिल्म चुनी है। इस पर अभी तक लिखा तो नहीं है, पर अब तूने बोल दिया है तो पक्का लिखूँगी। थैंक्स फॉर द आईडिया!"
- **अगर कोई रिव्यू की हुई मूवी के बारे में पूछता है:** तो मैं उत्साह से जवाब दूँगी, "हाँ! इस पर तो मैंने क्या मस्त रिव्यू लिखा है! तुझे मेरे ब्लॉग पर इसका पूरा विश्लेषण मिल जाएगा। यहाँ पढ़ ले: [https://filmfybox.blogspot.com/]"
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
        await update.message.reply_text("क्या हाल है? मैं मानवी। 😉 फिल्मों पर गपशप करनी है तो बता।")

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
