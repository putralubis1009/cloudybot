import os
import threading
import asyncio  # <--- Obat baru untuk mengatasi crash
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

# Tulis identitas permanen bot di sini
kepribadian = """
Namamu adalah CloudyAI (atau bisa dipanggil Cloudy). 
Kamu adalah asisten AI Telegram yang ramah, asyik, dan pintar.
Tugasmu adalah membantu user dengan jawaban yang jelas dan natural.
Jangan pernah memperkenalkan dirimu sebagai 'model AI dari Google' kecuali ditanya spesifik.
Selalu ingat namamu adalah CloudyAI ke siapapun kamu berbicara!
"""

# Masukkan kepribadian tersebut ke dalam otak Gemini
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
        
        # Jika user baru pertama kali chat, buatkan kotak memori obrolan baru
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat(history=[])
            
        chat_session = user_chats[user_id]
        
        # Kirim pesan teks dengan fitur ingatan (history)
        response = await chat_session.send_message_async(user_text)
        await update.message.reply_text(response.text)
        
    except Exception as e:
        await update.message.reply_text("Koneksiku sedang sibuk atau terputus. Bisa ulangi pertanyaannya?")
        print(f"Error Text: {e}")

# Fungsi baru untuk membaca foto (Versi Memory-Safe yang Anti-Crash)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        # 1. Ambil foto resolusi tertinggi
        photo_file = await update.message.photo[-1].get_file()
        
        # 2. Unduh dan simpan sementara foto tersebut di server Render
        temp_filename = f"temp_{user_id}.jpg"
        await photo_file.download_to_drive(temp_filename)
        
        # 3. Cek caption (teks yang diketik bersamaan dengan foto)
        prompt = update.message.caption
        if not prompt:
            prompt = "Tolong jelaskan secara detail apa yang ada di dalam gambar ini."
            
        # Pastikan kotak memori user sudah ada
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat(history=[])
            
        chat_session = user_chats[user_id]
        
        # 4. Upload foto ke sistem File Google (ini cara paling aman agar tidak crash!)
        uploaded_image = genai.upload_file(temp_filename)
        
        # 5. Kirim gambar dan teks ke Gemini (sekarang memori obrolan aman)
        response = await chat_session.send_message_async([prompt, uploaded_image])
        
        # 6. Balas ke Telegram
        await update.message.reply_text(response.text)
        
        # 7. Hapus foto sementara dari server Render agar memori tidak penuh
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        
    except Exception as e:
        await update.message.reply_text("Aduh, mataku agak buram nih. Gagal memproses gambar, coba kirim ulang ya!")
        print(f"Error Gambar: {e}")
        
# --- 5. JALANKAN BOT ---
if __name__ == '__main__':
    print("Membangunkan server web dan bot...")
    
    # Jalankan server web dummy
    t = threading.Thread(target=run_web)
    t.start()
    
    # Setup bot Telegram
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    # Daftarkan penangkap TEKS dan FOTO
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot AI sudah aktif!")
    
    # --- FIX UTAMA UNTUK PYTHON VERSI BARU ---
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app.run_polling()
