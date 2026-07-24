import os
import threading
import asyncio
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import io
from PIL import Image

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

# --- 3. SETUP GEMINI & KEPRIBADIAN ---
genai.configure(api_key=GEMINI_API_KEY)

kepribadian = """
Namamu adalah CloudyAI (atau bisa dipanggil Cloudy). 
Kamu adalah asisten AI Telegram yang ramah, asyik, dan pintar.
Tugasmu adalah membantu user dengan jawaban yang jelas dan natural.
Jangan pernah memperkenalkan dirimu sebagai 'model AI dari Google' kecuali ditanya spesifik.
Selalu ingat namamu adalah CloudyAI ke siapapun kamu berbicara!
"""

# Tetap menggunakan Gemini 3.6 Flash pilihanmu!
model = genai.GenerativeModel(
    'gemini-3.6-flash',
    system_instruction=kepribadian
)

# Memori untuk menyimpan obrolan masing-masing user
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
        
        # Menggunakan send_message biasa agar sinkron dengan library Google
        response = chat_session.send_message(user_text)
        await update.message.reply_text(response.text)
        
    except Exception as e:
        await update.message.reply_text("Koneksiku sedang sibuk atau terputus. Bisa ulangi pertanyaannya?")
        print(f"Error Text Detail: {e}", flush=True)

# Fungsi untuk membaca foto
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        photo_file = await update.message.photo[-1].get_file()
        temp_filename = f"temp_{user_id}.jpg"
        await photo_file.download_to_drive(temp_filename)
        
        prompt = update.message.caption
        if not prompt:
            prompt = "Tolong jelaskan secara detail apa yang ada di dalam gambar ini."
            
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat(history=[])
            
        chat_session = user_chats[user_id]
        
        uploaded_image = genai.upload_file(temp_filename)
        
        response = chat_session.send_message([prompt, uploaded_image])
        await update.message.reply_text(response.text)
        
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        
    except Exception as e:
        await update.message.reply_text("Aduh, mataku agak buram nih. Gagal memproses gambar, coba kirim ulang ya!")
        print(f"Error Gambar Detail: {e}", flush=True)

# --- 5. JALANKAN BOT ---
if __name__ == '__main__':
    print("Membangunkan server web dan bot...", flush=True)
    
    t = threading.Thread(target=run_web)
    t.start()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot AI sudah aktif!", flush=True)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app.run_polling()
