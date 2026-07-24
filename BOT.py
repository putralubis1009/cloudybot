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

# --- 3. SETUP KEPRIBADIAN & SEMUA DAFTAR MODEL ---
genai.configure(api_key=GEMINI_API_KEY)

kepribadian = """
Namamu adalah CloudyAI (atau bisa dipanggil Cloudy). 
Kamu adalah asisten AI Telegram yang ramah, asyik, dan pintar.
Tugasmu adalah membantu user dengan jawaban yang jelas dan natural.
Jangan pernah memperkenalkan dirimu sebagai 'model AI dari Google' kecuali ditanya spesifik.
Selalu ingat namamu adalah CloudyAI ke siapapun kamu berbicara!
"""

# Daftar seluruh model teks yang kamu miliki, diurutkan dari prioritas utama
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

# --- 4. FUNGSI TELEGRAM DENGAN AUTO-FALLBACK ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Aku Cloudy, bot AI dengan armada model cadangan super lengkap. Ayo ngobrol!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        respon_berhasil = None
        model_yang_pakai = ""
        
        # Otomatis mencoba model satu per satu dari atas ke bawah jika limit
        for nama_model in DAFTAR_MODEL:
            try:
                temp_model = genai.GenerativeModel(
                    nama_model,
                    system_instruction=kepribadian
                )
                
                chat_session = temp_model.start_chat(history=[])
                response = chat_session.send_message(user_text)
                
                respon_berhasil = response.text
                model_yang_pakai = nama_model
                break # Berhenti mencari kalau berhasil
                
            except Exception as err:
                print(f"Model {nama_model} limit/error, beralih ke model berikutnya...", flush=True)
                continue
        
        # Kirim jawaban jika ada model yang lolos
        if respon_berhasil:
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
    
    print("Bot AI sudah aktif dengan sistem All-Model Fallback!", flush=True)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app.run_polling(drop_pending_updates=True)
