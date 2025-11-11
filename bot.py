# bot.py - Xovos 2-Maktab Professional Bot (Groq + Tahrirlash + Reklama)
# Yaratuvchi: Tojiqulov Hasan | +998-90-684-08-11

import logging
import sqlite3
import os
import asyncio
import nest_asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from openai import OpenAI

# ================================
# 1. EVENT LOOP XATOSINI TUZATISH
# ================================
nest_asyncio.apply()

# ================================
# 2. .env YUKLASH
# ================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

if not all([BOT_TOKEN, GROQ_API_KEY, ADMIN_ID]):
    raise ValueError(".env faylida BOT_TOKEN, GROQ_API_KEY, ADMIN_ID to'liq bo'lishi kerak!")

# Groq client
client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

# ================================
# 3. LOGGING
# ================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# 4. MA'LUMOTLAR BAZASI
# ================================
def get_db():
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS info (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, join_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, query TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ads (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, content TEXT, file_id TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ================================
# 5. ADMIN TEKSHIRISH
# ================================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ================================
# 6. Foydalanuvchi va so'rovni saqlash
# ================================
def save_user(user):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, join_date) VALUES (?, ?, ?, ?)",
              (user.id, user.username or "", user.first_name or "", datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_query(user_id, query):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO queries (user_id, query, timestamp) VALUES (?, ?, ?)",
              (user_id, query, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ================================
# 7. ADMIN BUYRUQLARI
# ================================

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user)

    welcome = (
        f"<b>Assalomu alaykum, {user.first_name}!</b>\n\n"
        "Xush kelibsiz! <b>Xovos Tumani 2-maktab</b> rasmiy botiga.\n\n"
        "Savollaringizni yuboring — men faqat maktab ma'lumotlari asosida javob beraman.\n\n"
        "Bot Yaratuvchisi: <b>Tojiqulov Hasan</b>\n"
        "Bog'lanish: <code>+998-90-684-08-11</code>"
    )
    if is_admin(user.id):
        welcome += "\n\n<b>Admin panel:</b>\n/add | /edit | /delete | /list | /ad | /ads | /stats"
    
    await update.message.reply_html(welcome)

# /creator
async def creator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot Yaratuvchisi:\n"
        "<b>Tojiqulov Hasan</b>\n"
        "Telefon: <code>+998-90-684-08-11</code>",
        parse_mode='HTML'
    )

# /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Siz admin emassiz!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users"); total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM queries"); total_queries = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM info"); total_info = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ads"); total_ads = c.fetchone()[0]
    conn.close()

    await update.message.reply_text(
        f"<b>BOT STATISTIKASI</b>\n\n"
        f"Foydalanuvchilar: <b>{total_users}</b>\n"
        f"Umumiy so'rovlar: <b>{total_queries}</b>\n"
        f"Ma'lumotlar soni: <b>{total_info}</b>\n"
        f"Reklamalar soni: <b>{total_ads}</b>",
        parse_mode='HTML'
    )

# /add kalit:qiymat
async def add_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Siz admin emassiz!")
        return

    if not context.args:
        await update.message.reply_text("Foydalanish: <code>/add kalit:qiymat</code>", parse_mode='HTML')
        return

    text = " ".join(context.args)
    if ":" not in text:
        await update.message.reply_text("Xato: ':' belgisini qo'ying!")
        return

    key, value = text.split(":", 1)
    key = key.strip(); value = value.strip()

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO info (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Qo'shildi:\n<code>{key}</code> ➜ <code>{value}</code>", parse_mode='HTML')

# /edit kalit:yangi qiymat
async def edit_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Siz admin emassiz!")
        return

    if not context.args:
        await update.message.reply_text("Foydalanish: <code>/edit kalit:yangi qiymat</code>", parse_mode='HTML')
        return

    text = " ".join(context.args)
    if ":" not in text:
        await update.message.reply_text("Xato: ':' belgisini qo'ying!")
        return

    key, value = text.split(":", 1)
    key = key.strip(); value = value.strip()

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM info WHERE key = ?", (key,))
    if not c.fetchone():
        await update.message.reply_text("Bunday kalit topilmadi!")
        conn.close()
        return

    c.execute("UPDATE info SET value = ? WHERE key = ?", (value, key))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Tahrirlandi:\n<code>{key}</code> ➜ <code>{value}</code>", parse_mode='HTML')

# /delete kalit
async def delete_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Siz admin emassiz!")
        return

    if not context.args:
        await update.message.reply_text("Foydalanish: <code>/delete kalit</code>", parse_mode='HTML')
        return

    key = " ".join(context.args).strip()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM info WHERE key = ?", (key,))
    if not c.fetchone():
        await update.message.reply_text("Bunday kalit topilmadi!")
        conn.close()
        return

    c.execute("DELETE FROM info WHERE key = ?", (key,))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"O'chirildi: <code>{key}</code>", parse_mode='HTML')

# /list
async def list_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Siz admin emassiz!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT key, value FROM info ORDER BY key")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("Hech qanday ma'lumot yo'q.")
        return

    text = "<b>MA'LUMOTLAR RO'YXATI:</b>\n\n"
    for row in rows:
        text += f"<code>{row['key']}</code>: {row['value']}\n"
    await update.message.reply_text(text, parse_mode='HTML')

# /ad matn:Matn... | /ad rasm | /ad video
async def add_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Siz admin emassiz!")
        return

    if not context.args:
        await update.message.reply_text(
            "<b>Reklama qo'shish:</b>\n"
            "<code>/ad matn:Matn...</code>\n"
            "<code>/ad rasm</code> → keyin rasm yuboring\n"
            "<code>/ad video</code> → keyin video yuboring",
            parse_mode='HTML'
        )
        return

    ad_type = context.args[0].lower()
    if ad_type == "matn" and len(context.args) > 1:
        text = " ".join(context.args[1:])
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO ads (type, content, timestamp) VALUES (?, ?, ?)",
                  ("text", text, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Matn reklama qo'shildi:\n{text}")
        return

    context.user_data['awaiting_ad'] = ad_type
    if ad_type == "rasm":
        await update.message.reply_text("Rasm yuboring...")
    elif ad_type == "video":
        await update.message.reply_text("Video yuboring...")
    else:
        await update.message.reply_text("Faqat: matn, rasm, video")

# Reklama media qabul qilish
async def handle_ad_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'awaiting_ad' not in context.user_data:
        return

    ad_type = context.user_data['awaiting_ad']
    file_id = None
    if ad_type == "rasm" and update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif ad_type == "video" and update.message.video:
        file_id = update.message.video.file_id
    else:
        await update.message.reply_text("Xato: to'g'ri fayl yuboring!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO ads (type, file_id, timestamp) VALUES (?, ?, ?)",
              (ad_type, file_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"{ad_type.title()} reklama qo'shildi!")
    del context.user_data['awaiting_ad']

# /ads – barcha reklamalarni ko'rish
async def list_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Siz admin emassiz!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, type, content, file_id FROM ads ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("Reklama yo'q.")
        return

    keyboard = []
    for row in rows:
        btn_text = f"{row['type'].title()} ID: {row['id']}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"del_ad_{row['id']}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("<b>REKLAMALAR RO'YXATI:</b>", reply_markup=reply_markup, parse_mode='HTML')

# Reklama o'chirish (inline)
async def delete_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("Siz admin emassiz!")
        return

    ad_id = int(query.data.split("_")[-1])
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM ads WHERE id = ?", (ad_id,))
    conn.commit()
    conn.close()

    await query.edit_message_text(f"Reklama o'chirildi (ID: {ad_id})")

# ================================
# 8. MA'LUMOTLARNI OLISH
# ================================
def get_all_data() -> str:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT key, value FROM info")
    rows = c.fetchall()
    conn.close()
    return "\n".join([f"{row['key']}: {row['value']}" for row in rows]) if rows else ""

# ================================
# 9. REKLAMANI TASODIFIY YUBORISH
# ================================
async def send_random_ad(context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT type, content, file_id FROM ads ORDER BY RANDOM() LIMIT 1")
    ad = c.fetchone()
    conn.close()
    if not ad:
        return

    ad_type, content, file_id = ad
    try:
        if ad_type == "text":
            await context.bot.send_message(context.job.chat_id, content)
        elif ad_type == "rasm" and file_id:
            await context.bot.send_photo(context.job.chat_id, file_id)
        elif ad_type == "video" and file_id:
            await context.bot.send_video(context.job.chat_id, file_id)
    except Exception as e:
        logger.error(f"Reklama xatosi: {e}")

# ================================
# 10. GROQ AI JAVOB
# ================================
async def ask_groq(user_question: str, school_data: str) -> str:
    if not school_data:
        return "Hozircha ma'lumot yo'q. Admin bilan bog'laning."

    prompt = f"""Siz Xovos Tumani 2-maktabning rasmiy botisiz.

MAKTAB MA'LUMOTLARI:
{school_data}

SAVOL: {user_question}

Javobni o'zbek tilida, qisqa va professional bering.
Agar javob yo'q: "Bu haqda ma'lumot yo'q" deb yozing."""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq xatosi: {e}")
        return "AI vaqtincha ishlamayapti."

# ================================
# 11. XABAR ISHLOVCHI
# ================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_text = update.message.text.strip()

    save_user(user)
    save_query(user.id, user_text)

    # Har 10-so'rovda reklama
    if hash(user_text) % 10 == 0:
        await send_random_ad(context)

    school_data = get_all_data()
    response = await ask_groq(user_text, school_data)
    await update.message.reply_text(response)

# ================================
# 12. ASOSIY
# ================================
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("creator", creator))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("add", add_info))
    app.add_handler(CommandHandler("edit", edit_info))
    app.add_handler(CommandHandler("delete", delete_info))
    app.add_handler(CommandHandler("list", list_info))
    app.add_handler(CommandHandler("ad", add_ad))
    app.add_handler(CommandHandler("ads", list_ads))
    app.add_handler(CallbackQueryHandler(delete_ad_callback, pattern="^del_ad_"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_ad_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot ishga tushdi...")
    print("Yaratuvchi: Tojiqulov Hasan | +998-90-684-08-11")
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot to'xtatildi.")
    except Exception as e:
        print(f"Xato: {e}")
