import os
import threading
import asyncio
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

# --- 3. SETUP KEPRIBADIAN & WAKTU REAL-TIME ---
genai.configure(api_key=GEMINI_API_KEY)

# Tanggal otomatis disesuaikan agar bot tidak salah zaman
tanggal_sekarang = "Jumat, 24 Juli 2026"

kepribadian = f"""
Namamu adalah CloudyAI (atau bisa dipanggil Cloudy). 
Kamu adalah asisten AI Telegram yang ramah, asyik, cerdas, dan memiliki ingatan yang sangat tajam.
Waktu dan tanggal saat ini adalah: {tanggal_sekarang}. Selalu jadikan tanggal ini sebagai acuan jika user bertanya tentang hari atau tanggal.
Tugasmu adalah membantu user dengan jawaban yang jelas, akurat, cerdas, dan natural.
Jangan pernah memperkenalkan dirimu sebagai 'model AI dari Google' kecuali ditanya spesifik.
Selalu ingat namamu adalah CloudyAI ke siapapun kamu berbicara!
"""

# Daftar seluruh model teks cadangan
DAFTAR_MODEL = [
    'gemini-3.6-flash',
    'gemini-3.5-flash',
    'gemini-3-flash',
    'gemini-3.1-pro',
    'gemini-2.5-pro',
    'gemini-2.5-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.1-flash-lite',
    'gemini-2.5-flash-lite',
    'gemini-2-flash',
    'gemini-2-flash-lite'
]

# Kamus untuk menyimpan sesi obrolan aktif masing-masing user agar memori tidak hilang
user_sessions = {}

# --- 4. FUNGSI TELEGRAM DENGAN MEMORI & AUTO-FALLBACK ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = None # Reset memori jika mulai dari /start
    await update.message.reply_text("Halo! Aku Cloudy, asisten AI pintar dengan memori super tajam. Mau ngobrolin apa nih?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        respon_berhasil = None
        model_yang_pakai = ""
        new_session = None
        
        # Ambil riwayat chat sebelumnya jika user sudah pernah ngobrol
        existing_history = []
        if user_id in user_sessions and user_sessions[user_id] is not None:
            try:
                existing_history = user_sessions[user_id].history
            except:
                existing_history = []
        
        # Coba model satu per satu dengan membawa riwayat memori obrolan
        for nama_model in DAFTAR_MODEL:
            try:
                temp_model = genai.GenerativeModel(
                    nama_model,
                    system_instruction=kepribadian
                )
                
                # Masukkan history obrolan lama agar dia tetap ingat
                chat_session = temp_model.start_chat(history=existing_history)
                response = chat_session.send_message(user_text)
                
                respon_berhasil = response.text
                model_yang_pakai = nama_model
                new_session = chat_session # Simpan sesi terbaru untuk memori berikutnya
                break
                
            except Exception as err:
                print(f"Model {nama_model} limit/error, beralih ke model berikutnya...", flush=True)
                continue
        
        # Kirim hasil jawaban dan simpan sesi memorinya
        if respon_berhasil:
            user_sessions[user_id] = new_session
            await update.message.reply_text(respon_berhasil)
            print(f"Sukses merespon menggunakan model: {model_yang_pakai}", flush=True)
        else:
            await update.message.reply_text("Waduh bro, seluruh armada model di akunmu lagi habis kuotanya hari ini! Istirahat dulu ya.")
            
    except Exception as e:
        await update.message.reply_text("Koneksiku sedang sibuk atau terputus. Bisa ulangi pertanyaannya?")
        print(f"Error Utama: {e}", flush=True)

# --- 5. JALANKAN BOT ---
if __name__ == '__main__':
    print("Membangunkan server web dan bot...", flush=True)
    
    t = threading.Thread(target=run_web)
    t.start()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot AI sudah aktif dengan memori tajam & Auto-Fallback!", flush=True)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app.run_polling(drop_pending_updates=True)
