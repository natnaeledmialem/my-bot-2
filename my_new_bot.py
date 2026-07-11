import telebot
from telebot import types
from flask import Flask

# --- ማስተካከያ ቦታዎች ---
BOT_TOKEN = "8992506840:AAHu0cy3sWdiZvSfIhBJRrujyUhCXNt8tGE"
CHANNELS = ["@ghhggghhhgg", "@works_11w", "@aa_11_b1", "@samiworkers"] 
ADMIN_ID = 8465808385
ADMIN_USERNAME = "samuel16nm" 
REFERRAL_BONUS = 4.00 
MIN_WITHDRAW = 25.00  
# ---------------------

bot = telebot.TeleBot(BOT_TOKEN)
users_db = {}

def check_status(user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            return False
    return True

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

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("💰 አካውንቴ (Balance)")
    btn2 = types.KeyboardButton("🔗 መጋበዣ ሊንክ (Referral)")
    btn3 = types.KeyboardButton("💵 ብር ማውጫ (Withdraw)")
    btn4 = types.KeyboardButton("👨‍💻 ደንበኞች አገልግሎት (Support)")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "ተጠቃሚ"
    
    if user_id not in users_db:
        users_db[user_id] = {'balance': 0.0, 'referred_by': None, 'referred_count': 0}
        args = message.text.split()
        if len(args) > 1:
            referrer_id = int(args[1])
            if referrer_id in users_db and referrer_id != user_id:
                users_db[user_id]['referred_by'] = referrer_id

    not_joined = get_not_joined_channels(user_id)
    
    if not_joined:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, ch in enumerate(not_joined, 1):
            url_link = f"https://t.me/{ch.replace('@', '')}"
            markup.add(types.InlineKeyboardButton(f"📢 ቻናል {i}ን ተቀላቀል", url=url_link))
        
        markup.add(types.InlineKeyboardButton("✅ ተቀላቅያለሁ (Check)", callback_data="check_join"))
        
        bot.send_message(
            user_id, 
            f"👋 **ሰላም {username}!**\n\nቦቱን ለመጠቀም መጀመሪያ ሁሉንም ቻናሎቻችንን መቀላቀል አለብዎት።👇", 
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    ref_id = users_db[user_id]['referred_by']
    if ref_id and users_db[user_id]['referred_count'] == 0:
        users_db[ref_id]['balance'] += REFERRAL_BONUS
        users_db[ref_id]['referred_count'] += 1
        users_db[user_id]['referred_count'] = -1
        try:
            bot.send_message(ref_id, f"🎉 **አዲስ ሰው ጋብዘዋል!**\n+{REFERRAL_BONUS} ብር ወደ አካውንትዎ ተጨምሯል።", parse_mode="Markdown")
        except:
            pass

    bot.send_message(
        user_id, 
        "✨ **እንኳን በደህና መጡ!**\n\nከታች ያሉትን ቁልፎች በመጠቀም ሰዎችን ይጋብዙ እና ያትርፉ።", 
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

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
        text = f"💳 **የአካውንትዎ መረጃ**\n\n💵 **ጠቅላላ ቀሪ ሂሳብ፦** {bal:.2f} ብር\n👥 **የጋበዟቸው ሰዎች ቁጥር፦** {count} ሰው"
        bot.send_message(user_id, text, parse_mode="Markdown")

    elif message.text == "🔗 መጋበዣ ሊንክ (Referral)":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        text = f"👥 **ሰዎችን ይጋብዙ!**\n\nየእርስዎ መጋበዣ ሊንክ ይህ ነው👇\n`{ref_link}`\n\n🎁 አንድ ሰው በሊንክዎ ሲገባ **{REFERRAL_BONUS} ብር** ያገኛሉ።"
        bot.send_message(user_id, text, parse_mode="Markdown")

    elif message.text == "💵 ብር ማውጫ (Withdraw)":
        bal = users_db[user_id]['balance']
        if bal < MIN_WITHDRAW:
            bot.send_message(user_id, f"❌ **ይቅርታ፣ ብር ለማውጣት ቢያንስ {MIN_WITHDRAW} ብር ሊኖርዎት ይገባል።**\n\n💵 የእርስዎ ሂሳብ፦ {bal:.2f} ብር", parse_mode="Markdown")
        else:
            msg = bot.send_message(user_id, "🔄 **እባክዎ ብሩ የሚገባበትን ስም እና ስልክ ቁጥር (ወይም የባንክ አካውንት) ይጻፉልን፦**", parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_withdraw)

    elif message.text == "👨‍💻 ደንበኞች አገልግሎት (Support)":
        markup = types.InlineKeyboardMarkup()
        support_button = types.InlineKeyboardButton("💬 በውስጥ መስመር አግኘኝ", url=f"https://t.me/{ADMIN_USERNAME}")
        markup.add(support_button)
        text = "💁‍♂️ **ማንኛውም አይነት ጥያቄ፣ አስተያየት ወይም የክፍያ ችግር ካጋጠመዎት ከታች ያለውን ቁልፍ ተጭነው ያግኙን።**"
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

def process_withdraw(message):
    user_id = message.from_user.id
    details = message.text
    bal = users_db[user_id]['balance']
    username = message.from_user.username or "የሌለው"

    users_db[user_id]['balance'] = 0.0

    admin_msg = (f"🚨 **አዲስ የማውጫ ጥያቄ ደርሷል!**\n\n"
                 f"👤 ተጠቃሚ ID: `{user_id}`\n"
                 f"🏷 ዩዘርኔም: @{username}\n"
                 f"💰 የሚወጣው ብር: {bal:.2f} ብር\n"
                 f"📌 ዝርዝር መረጃ: {details}")
    
    bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    bot.send_message(user_id, "✅ **ጥያቄዎ በተሳካ ሁኔታ ለባለቤቱ ተልኳል! በአጭር ጊዜ ውስጥ ይላክልዎታል።**", parse_mode="Markdown")

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
