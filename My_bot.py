import telebot
from telebot import types
from flask import Flask

# --- ማስተካከያ ቦታዎች ---
BOT_TOKEN = "8992506840:AAFn6dSKy12F3kR10YW0EBO0efjfN8wC2lE"
# ሁሉንም ቻናሎች እዚህ ዝርዝር ውስጥ ብቻ አስገባ! ቦቱ በሙሉ Admin መሆን አለበት።
CHANNELS = ["@ghhggghhhgg", "@works_11w", "@aa_11_b1", "@samiworkers"] 
ADMIN_ID = 8465808385
REFERRAL_BONUS = 3.00 # ለአንድ ሰው መጋበዣ የሚከፈለው የብር መጠን
MIN_WITHDRAW = 30.00  # ዝቅተኛው የማውጫ መጠን
# ---------------------

bot = telebot.TeleBot(BOT_TOKEN)

# የሰዎችን ብር እና መረጃ መመዝገቢያ
users_db = {}

# ሁሉንም ቻናሎች በአንድነት ቼክ ማድረጊያ ተግባር
def check_status(user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False  # አንዱንም እንኳ Join ካላደረገ False ይመልሳል
        except Exception:
            return False  # ስህተት ቢፈጠር (ለምሳሌ ቦቱ አድሚን ካልሆነ) False
    return True  # ሁሉንም Join ካደረገ ብቻ True ይመልሳል

# ተጠቃሚው ያልገባባቸውን ቻናሎች ለይቶ ማውጫ
def get_not_joined_channels(user_id):
    not_joined = []
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(channel)
        except Exception:
            not_joined.append(channel)
    return not_joined

# ዋናው ማውጫ (Keyboard)
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💰 አካውንቴ (Balance)")
    btn2 = types.KeyboardButton("🔗 መጋበዣ ሊንክ (Referral)")
    btn3 = types.KeyboardButton("💵 ብር ማውጫ (Withdraw)")
    markup.add(btn1, btn2)
    markup.add(btn3)
    return markup

# /start ሲጫኑ
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "ተጠቃሚ"
    
    # አዲስ ተጠቃሚ ከሆነ በሲስተሙ መመዝገብ
    if user_id not in users_db:
        users_db[user_id] = {'balance': 0.0, 'referred_by': None, 'referred_count': 0}
        
        # በሪፈራል ሊንክ የገባ ከሆነ መመዝገብ (ብሩ የሚታሰበው ቻናሉን ሲቀላቀል ነው)
        args = message.text.split()
        if len(args) > 1:
            referrer_id = int(args[1])
            if referrer_id in users_db and referrer_id != user_id:
                users_db[user_id]['referred_by'] = referrer_id

    # ቻናሎቹን መፈተሽ
    not_joined = get_not_joined_channels(user_id)
    
    # Join ያላደረጉት ቻናል ካለ ማስገደጃ በተን መላክ
    if not_joined:
        markup = types.InlineKeyboardMarkup()
        
        # ለእያንዳንዱ ያልገቡበት ቻናል የመግቢያ ሊንክ በተን ይፈጥራል
        for i, ch in enumerate(not_joined, 1):
            url_link = f"https://t.me/{ch.replace('@', '')}"
            markup.add(types.InlineKeyboardButton(f"📢 ቻናል {i}ን ተቀላቀል", url=url_link))
        
        # ሁሉንም ካጠናቀቁ በኋላ ቼክ ማድረጊያ በተን
        markup.add(types.InlineKeyboardButton("✅ ተቀላቅያለሁ (Check)", callback_data="check_join"))
        
        bot.send_message(
            user_id, 
            f"👋 ሰላም {username}!\n\nቦቱን ለመጠቀም መጀመሪያ ሁሉንም ቻናሎቻችንን መቀላቀል አለብዎት።", 
            reply_markup=markup
        )
        return

    # ተቀላቅሎ ከሆነ እና እስካሁን የሪፈራል ብር ካልተሰጠ ማከፋፈል
    ref_id = users_db[user_id]['referred_by']
    if ref_id and users_db[user_id]['referred_count'] == 0:
        users_db[ref_id]['balance'] += REFERRAL_BONUS
        users_db[ref_id]['referred_count'] += 1
        users_db[user_id]['referred_count'] = -1  # ብሩ ድጋሚ እንዳይታሰብ
        try:
            bot.send_message(ref_id, f"🎉 አዲስ ሰው ጋብዘዋል! +{REFERRAL_BONUS} ብር ወደ አካውንትዎ ተጨምሯል።")
        except:
            pass

    bot.send_message(user_id, "እንኳን በደህና መጡ! ከታች ያሉትን ቁልፎች በመጠቀም ይጋብዙ እና ያትርፉ።", reply_markup=main_keyboard())

# Check Button ሲጫኑ
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_callback(call):
    user_id = call.from_user.id
    if check_status(user_id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ አሁንም ሁሉንም ቻናሎች አልተቀላቀሉም!", show_alert=True)

# ፅሁፎችን ማስተናገጃ (Buttons)
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id
    
    if user_id not in users_db:
        bot.send_message(user_id, "እባክዎ መጀመሪያ /start ይበሉ")
        return

    if not check_status(user_id):
        start(message)
        return

    if message.text == "💰 አካውንቴ (Balance)":
        bal = users_db[user_id]['balance']
        count = max(0, users_db[user_id]['referred_count'])
        bot.send_message(user_id, f"💳 **የአካውንትዎ መረጃ**\n\n💵 ጠቅላላ ቀሪ ሂሳብ፦ {bal} ብር\n👥 የጋበዟቸው ሰዎች ቁጥር፦ {count}")

    elif message.text == "🔗 መጋበዣ ሊንክ (Referral)":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(user_id, f"👥 **ሰዎችን ይጋብዙ!**\n\nየእርስዎ መጋበዣ ሊንክ ይህ ነው👇\n{ref_link}\n\nአንድ ሰው በሊንክዎ ሲገባ **{REFERRAL_BONUS} ብር** ያገኛሉ።")

    elif message.text == "💵 ብር ማውጫ (Withdraw)":
        bal = users_db[user_id]['balance']
        if bal < MIN_WITHDRAW:
            bot.send_message(user_id, f"❌ ይቅርታ፣ ብር ለማውጣት ቢያንስ **{MIN_WITHDRAW} ብር** ሊኖርዎት ይገባል።\n💵 የእርስዎ ሂሳብ፦ {bal} ብር")
        else:
            msg = bot.send_message(user_id, "🔄 እባክዎ ብሩ የሚገባበትን ስም እና ስልክ ቁጥር (ወይም የባንክ አካውንት) ይጻፉልን፦")
            bot.register_next_step_handler(msg, process_withdraw)

# የዊዝድሮው ሂደት
def process_withdraw(message):
    user_id = message.from_user.id
    details = message.text
    bal = users_db[user_id]['balance']
    username = message.from_user.username or "የሌለው"

    # ብሩን መቀነስ
    users_db[user_id]['balance'] = 0.0

    # ለባለቤቱ (Admin) መልዕክት መላክ
    admin_msg = (f"🚨 **አዲስ የማውጫ ጥያቄ ደርሷል!**\n\n"
                 f"👤 ተጠቃሚ ID: `{user_id}`\n"
                 f"🏷 ዩዘርኔም: @{username}\n"
                 f"💰 የሚወጣው ብር: {bal} ብር\n"
                 f"📌 ዝርዝር መረጃ: {details}")
    
    bot.send_message(ADMIN_ID, admin_msg)
    bot.send_message(user_id, "✅ ጥያቄዎ በተሳካ ሁኔታ ለባለቤቱ ተልኳል! በአጭር ጊዜ ውስጥ ይላክልዎታል።")

# ቦቱን ማስጀመር
print("ቦቱ እየሰራ ነው...")
bot.delete_webhook(drop_pending_updates=True)

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    from threading import Thread
    Thread(target=run_flask).start()
    
    print("Bot is polling...")
    bot.infinity_polling(skip_pending=True)
