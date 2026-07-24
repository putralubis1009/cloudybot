import os
import threading
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. AMBIL KUNCI DARI ENVIRONMENT VARIABLES (AMAN) ---
# Tidak ada lagi teks kunci asli di sini!
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- 2. SETUP SERVER DUMMY UNTUK RENDER ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot Telegram sedang berjalan!"

def run_web():
    # Render akan memberikan port secara otomatis
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

# --- 3. SETUP AI GEMINI ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Catatan: versi yang valid saat ini biasanya 1.5-flash

# --- 4. FUNGSI TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Aku bot AI. Ayo ngobrol!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Koneksiku sempat terputus sebentar, bisa ulangi pertanyaannya?")
        print(f"Error: {e}")

# --- 5. JALANKAN BOT & SERVER ---
if __name__ == '__main__':
    print("Membangunkan server web dan bot...")
    
    # Jalankan server web Flask di latar belakang (Thread)
    t = threading.Thread(target=run_web)
    t.start()
    
    # Jalankan Bot Telegram
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot AI sudah aktif!")
    app.run_polling()