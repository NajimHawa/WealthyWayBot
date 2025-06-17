import sqlite3
import random
import string
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7740977168:AAH-Tr9yqhm6TDi9naDP12O_HMGtc5o_9xc"

# إنشاء قاعدة بيانات SQLite
conn = sqlite3.connect("wealthyway.db", check_same_thread=False)
cursor = conn.cursor()

# إنشاء جدول المستخدمين إذا لم يكن موجودًا
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    referral_code TEXT UNIQUE,
    balance REAL DEFAULT 0
)
''')
conn.commit()

def generate_referral_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def add_or_get_user(user_id, username):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if user:
        return user
    else:
        while True:
            code = generate_referral_code()
            cursor.execute("SELECT * FROM users WHERE referral_code=?", (code,))
            if not cursor.fetchone():
                break
        cursor.execute(
            "INSERT INTO users (user_id, username, referral_code, balance) VALUES (?, ?, ?, ?)",
            (user_id, username, code, 5)  # 5 دولار ترحيب
        )
        conn.commit()
        return (user_id, username, code, 5)

def add_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else 0

def get_referral_code(user_id):
    cursor.execute("SELECT referral_code FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else None

def get_user_by_referral(code):
    cursor.execute("SELECT * FROM users WHERE referral_code=?", (code,))
    return cursor.fetchone()

# دوال الأوامر بصيغة async

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    ref_code = args[0] if args else None

    user_data = add_or_get_user(user.id, user.username or user.full_name)

    if ref_code and ref_code != get_referral_code(user.id):
        ref_user = get_user_by_referral(ref_code)
        if ref_user:
            add_balance(ref_user[0], 5)  # 5 دولار إضافية للمُحيل
            await update.message.reply_text(
                f"تم تسجيلك بنجاح! لديك 5 دولار ترحيب.\n"
                f"شكرًا لدعوة صديقك! محيلك حصل على 5 دولار إضافية."
            )
        else:
            await update.message.reply_text(
                "رمز الإحالة غير صحيح، تم تسجيلك بدون إحالة.\nلديك 5 دولار ترحيب."
            )
    else:
        await update.message.reply_text(f"مرحبًا {user.first_name}! تم تسجيلك بنجاح.\nلديك 5 دولار ترحيب.")

    code = get_referral_code(user.id)
    await update.message.reply_text(f"كود الإحالة الخاص بك: {code}\nشارك هذا الكود مع أصدقائك!")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bal = get_balance(user.id)
    await update.message.reply_text(f"رصيدك الحالي هو: ${bal:.2f}")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT 5")
    top_users = cursor.fetchall()
    msg = "قائمة المتصدرين:\n"
    for i, (username, balance) in enumerate(top_users, 1):
        msg += f"{i}. @{username or 'مستخدم'} - ${balance:.2f}\n"
    await update.message.reply_text(msg)

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bal = get_balance(user.id)
    if bal >= 200:
        await update.message.reply_text("يمكنك الآن طلب السحب. سيتم التواصل معك قريبًا لإكمال العملية.")
        # هنا يمكن إضافة نظام طلب السحب البنكي لاحقًا
    else:
        await update.message.reply_text(f"رصيدك ${bal:.2f} أقل من الحد الأدنى للسحب (200 دولار).")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("withdraw", withdraw))

    print("البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
