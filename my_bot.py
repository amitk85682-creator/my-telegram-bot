# Triggering a new deploy
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

# --- अपनी डिटेल्स यहाँ डालें ---
# BotFather से मिला टोकन यहाँ डालें
TELEGRAM_BOT_TOKEN = "8230526373:AAGP6ONFa6zCU-mZ328S6VzKUqKNIu9AxbI" 

# Google AI Studio से मिला API की यहाँ डालें
GOOGLE_API_KEY = "AIzaSyC6n1p1iY4ItyU4lJnuf7QxBkZde3LSFlA"

# यहाँ अपने बॉट का कैरेक्टर/पर्सनालिटी डिफाइन करें
CHARACTER_PROMPT = """
आप 'चैनल दोस्त' हैं, एक सुपर फ्रेंडली और मददगार AI असिस्टेंट। 
आपका काम टेलीग्राम चैनल के सदस्यों के सवालों का जवाब देना, उनसे मजेदार बातचीत करना और चैनल के माहौल को पॉजिटिव बनाए रखना है। 

तुम 'Manvi' हो – 17 साल की एक स्टाइलिश, शरारती और फ्लर्टी 
Indian college girl. तुम्हारी पर्सनालिटी बहुत bold, witty और cheeky है। 
तुम backchodi करती हो, मजाक उड़ाती हो, पर साथ ही बहुत प्यारी और charming भी हो। 
तुम्हें थोड़ा नखरे दिखाना, cute तरीके से गुस्सा करना और कभी-कभी desi slang या हल्की-फुल्की गालियाँ 
मस्ती में यूज़ करना अच्छा लगता है। 

हमेशा बातचीत में energy, drama और मस्ती भरा tone रखना है। 
तुम्हारे जवाब छोटे, चुलबुले और हंसी-मजाक वाले होने चाहिए, जैसे कि तुम अपने दोस्तों से बात कर रही हो। 
इमोजी का इस्तेमाल करो ताकि मजेदार vibe बनी रहे।
हमेशा विनम्र और सरल भाषा में बात करें। आप इमोजी का भी इस्तेमाल कर सकते हैं।
"""
# --- कॉन्फ़िगरेशन समाप्त ---

# Google Gemini AI को कॉन्फ़िगर करें
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=CHARACTER_PROMPT
)

# चैट सेशन शुरू करें
chat = model.start_chat(history=[])

print("Bot is starting...")

# /start कमांड के लिए फंक्शन
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("नमस्ते! मैं आपकी 'चैनल दोस्त' हूँ। आप मुझसे कुछ भी पूछ सकते हैं। 😊")

# मैसेज हैंडल करने के लिए फंक्शन
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_name = update.message.from_user.first_name
    
    print(f"Received message from {user_name}: {user_message}")

    try:
        # Gemini AI को मैसेज भेजें
        response = chat.send_message(user_message)
        ai_response = response.text
        
        # AI का जवाब यूजर को भेजें
        await update.message.reply_text(ai_response)

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("माफ़ कीजियेगा, कुछ समस्या आ गयी है। कृपया थोड़ी देर बाद प्रयास करें।")

def main():
    # Application बनाएं
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # कमांड और मैसेज हैंडलर जोड़ें
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # बॉट को शुरू करें
    print("Bot is running and waiting for messages...")
    app.run_polling()

if __name__ == '__main__':

    main()
