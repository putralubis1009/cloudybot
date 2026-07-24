import os
import threading
import asyncio  # <--- Obat baru untuk mengatasi crash
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. AMBIL KUNCI ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- 2. SERVER DUMMY UNTUK RENDER ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot Telegram sedang berjalan!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

# --- 3. SETUP GEMINI & MEMORI OBROLAN ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.6-flash')

user_chats = {}

# --- 4. FUNGSI TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Aku Cloudy, bot AI pintar dengan memori super. Ayo ngobrol!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat(history=[])
            
        chat_session = user_chats[user_id]
        response = await chat_session.send_message_async(user_text)
        await update.message.reply_text(response.text)
        
    except Exception as e:
        await update.message.reply_text("Koneksiku sedang sibuk atau terputus. Bisa ulangi pertanyaannya?")
        print(f"Error: {e}")

# --- 5. JALANKAN BOT ---
if __name__ == '__main__':
    print("Membangunkan server web dan bot...")
    
    t = threading.Thread(target=run_web)
    t.start()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot AI sudah aktif!")
    
    # --- FIX UTAMA UNTUK PYTHON VERSI BARU ---
    # Kita buatkan jalur antrean secara manual agar Telegram tidak bingung
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app.run_polling()
