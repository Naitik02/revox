import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import os
import database
from datetime import datetime, timedelta

# --- MONKEY PATCH InlineKeyboardButton for API 9.4 'style' support ---
original_init = InlineKeyboardButton.__init__
def new_init(self, *args, **kwargs):
    self.style = kwargs.pop('style', None)
    original_init(self, *args, **kwargs)

original_to_dict = InlineKeyboardButton.to_dict
def new_to_dict(self):
    d = original_to_dict(self)
    if getattr(self, 'style', None):
        d['style'] = self.style
    return d

InlineKeyboardButton.__init__ = new_init
InlineKeyboardButton.to_dict = new_to_dict
# ---------------------------------------------------------------------

user_states = {} # To keep track of deposit flow state

# --- Configuration ---
BOT_TOKEN = "8989409928:AAGLBtV23Jleyn7BQr3AL3PV3Cw8VwNDLpA"
OWNER_ID = 8242625888
ADMIN_IDS = [8242625888, 7353874683]
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()

def get_current_admin_url():
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        return render_url + "/"
        
    if os.path.exists("public_url.txt"):
        with open("public_url.txt", "r") as f:
            url = f.read().strip()
            if url:
                return url
    return f"http://{LOCAL_IP}:5000/"

FORCE_JOIN_CHANNEL_ID = "-1003557330206"
FORCE_JOIN_CHANNEL_LINK = "https://t.me/digitaal_store"

bot = telebot.TeleBot(BOT_TOKEN)

def check_membership(user_id, username="Unknown"):
    try:
        # Update user in db automatically
        database.update_user_balance(user_id, 0.0, username)
        
        member = bot.get_chat_member(FORCE_JOIN_CHANNEL_ID, user_id)
        if member.status in ['left', 'kicked']:
            return False
        return True
    except Exception as e:
        print(f"Error checking membership: {e}")
        # If bot is not admin in the channel, it might throw an error. 
        # Make sure to promote the bot to admin in the channel!
        return False

# --- Handlers ---

def get_main_menu(user):
    user_name = user.first_name
    if user.last_name:
        user_name += f" {user.last_name}"
        
    welcome_text = (
        f"👋 Welcome, <a href='tg://user?id={user.id}'>{user_name}</a>!\n\n"
        f"🚀 <b>WELCOME TO REVOX STORE</b> 🚀\n\n"
        f"⚡ Fast\n"
        f"🔒 Secure\n"
        f"✅ Reliable\n\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"💎 <b>Premium AI & Digital Services</b>\n\n"
        f"• ChatGPT Plus\n"
        f"• ChatGPT GO\n"
        f"• GPT PRO CDKs\n"
        f"• Super Grok\n"
        f"• Claude Pro\n"
        f"• Perplexity Pro\n"
        f"• X Premium\n\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"📦 Instant Delivery\n"
        f"🛡️ Full Warranty\n"
        f"⚙️ Trusted Service\n\n"
        f"📩 Contact Support: @Meow_7737\n\n"
        f"Thank you for choosing REVOX STORE 🚀"
    )
    
    markup = InlineKeyboardMarkup()
    btn_shop = InlineKeyboardButton("🛍 Shop", callback_data="shop", style="primary")
    btn_deposit = InlineKeyboardButton("💲 Deposit", callback_data="deposit", style="success")
    btn_profile = InlineKeyboardButton("👤 Profile", callback_data="profile", style="primary")
    btn_orders = InlineKeyboardButton("🧾 My Orders", callback_data="orders", style="success")
    btn_help = InlineKeyboardButton("🎧 Help/Support", callback_data="support", style="danger")
    
    markup.row(btn_shop, btn_deposit)
    markup.row(btn_profile, btn_orders)
    markup.row(btn_help)
    
    if user.id in ADMIN_IDS:
        btn_admin = InlineKeyboardButton("⚙️ ADMIN PANEL", url=get_current_admin_url(), style="primary")
        markup.row(btn_admin)
        
    return welcome_text, markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    user_name = user.first_name
    if user.last_name:
        user_name += f" {user.last_name}"
        
    if not check_membership(user.id, user_name):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Join Channel", url=FORCE_JOIN_CHANNEL_LINK, style="primary"))
        markup.add(InlineKeyboardButton("✅ I Joined", callback_data="check_join", style="success"))
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Access Denied!</b>\n\nYou must join our official channel to use this bot.",
            reply_markup=markup,
            parse_mode="HTML"
        )
        return
        
    text, markup = get_main_menu(user)
    bot.send_message(
        message.chat.id, 
        text, 
        reply_markup=markup, 
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def handle_check_join(call):
    if check_membership(call.from_user.id):
        # Once joined, show the main menu
        call.message.from_user = call.from_user
        text, markup = get_main_menu(call.from_user)
        bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet! Please join to continue.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def handle_main_menu(call):
    bot.answer_callback_query(call.id)
    text, markup = get_main_menu(call.from_user)
    if call.message.content_type == 'text':
        try:
            bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            pass
    else:
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if not check_membership(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)
        return
        
    def get_back_markup():
        m = InlineKeyboardMarkup()
        m.add(InlineKeyboardButton("🏠 Back", callback_data="main_menu", style="danger"))
        return m
        
    def update_msg(text, markup):
        if call.message.content_type == 'text':
            try:
                bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception:
                pass
        else:
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
        
    if call.data == "shop":
        products = database.get_products()
        if not products:
            bot.answer_callback_query(call.id, "No products available.")
            update_msg("🛒 <b>Shop</b>\n\nNo products are currently available in the store.", get_back_markup())
            return
            
        bot.answer_callback_query(call.id, "Welcome to the Shop!")
        shop_markup = InlineKeyboardMarkup()
        styles = ["primary", "danger"]
        for i, p in enumerate(products):
            btn = InlineKeyboardButton(f"📦 {p['title']} - ${p['price']:.2f}", callback_data=f"buy_{p['id']}", style=styles[i % 2])
            shop_markup.add(btn)
        
        shop_markup.add(InlineKeyboardButton("🏠 Back", callback_data="main_menu", style="danger"))
        update_msg("🛒 <b>Shop</b>\n\nSelect a product to view details:", shop_markup)
        
    elif call.data.startswith("buy_"):
        product_id = int(call.data.replace("buy_", ""))
        product = database.get_product_by_id(product_id)
        if not product:
            bot.answer_callback_query(call.id, "Product not found!")
            return
            
        if product['stock_count'] <= 0:
            bot.answer_callback_query(call.id, "❌ Out of stock!", show_alert=True)
            return
            
        users = database.get_all_users()
        user = next((u for u in users if u['id'] == call.from_user.id), None)
        balance = user['balance'] if user else 0.0
        
        if balance < product['price']:
            bot.answer_callback_query(call.id, "❌ Insufficient balance! Please deposit funds.", show_alert=True)
            return
            
        stock = database.get_unsold_stock(product_id)
        if not stock:
            bot.answer_callback_query(call.id, "❌ Out of stock!", show_alert=True)
            return
            
        # Process Purchase
        database.update_user_balance(call.from_user.id, -product['price'])
        database.mark_stock_sold(stock['id'])
        
        now = datetime.now()
        duration_ends_at = (now + timedelta(days=product['duration_days'])).isoformat() if product.get('duration_days') else None
        warranty_ends_at = (now + timedelta(days=product['warranty_days'])).isoformat() if product.get('has_warranty') and product.get('warranty_days') else None
        warranty_text = "Yes" if product.get('has_warranty') else "No"
            
        database.create_order(call.from_user.id, product_id, stock['credentials'], warranty_text, duration_ends_at, warranty_ends_at)
        
        bot.answer_callback_query(call.id, "✅ Purchase successful!", show_alert=True)
        
        msg = f"🎉 <b>Purchase Successful!</b>\n\n"
        msg += f"🛍 <b>Product:</b> {product['title']}\n"
        msg += f"🔑 <b>Credentials:</b>\n<code>{stock['credentials']}</code>\n\n"
        msg += f"🛡 <b>Warranty:</b> {warranty_text}\n"
        msg += "Thank you for shopping at Revox Store!"
        
        bot.send_message(call.from_user.id, msg, parse_mode="HTML")
        update_msg("✅ <b>Purchase Complete</b>\n\nCheck your DMs for the credentials!", get_back_markup())
    elif call.data == "deposit":
        bot.answer_callback_query(call.id)
        users = database.get_all_users()
        user_balance = 0.0
        for u in users:
            if u['id'] == call.from_user.id:
                user_balance = u['balance']
                
        text = f"💰 <b>Deposit Funds</b>\n\nYou have currently: <b>${user_balance:.2f}</b>\n\nChoose an option below:"
        m = InlineKeyboardMarkup()
        m.add(InlineKeyboardButton("➕ Add Deposit", callback_data="add_deposit", style="success"))
        m.add(InlineKeyboardButton("📋 Check Previous Transactions", callback_data="check_tx_0", style="primary"))
        m.add(InlineKeyboardButton("🏠 Back", callback_data="main_menu", style="danger"))
        update_msg(text, m)
        
    elif call.data.startswith("check_tx_"):
        bot.answer_callback_query(call.id)
        page = int(call.data.split("_")[2])
        txs = database.get_transactions_by_user(call.from_user.id)
        
        if not txs:
            update_msg("📋 <b>Previous Transactions</b>\n\nYou have no transactions.", get_back_markup())
            return
            
        # Pagination (10 per page)
        start_idx = page * 10
        end_idx = start_idx + 10
        page_txs = txs[start_idx:end_idx]
        
        text = f"📋 <b>Previous Transactions (Page {page+1})</b>\n\n"
        for t in page_txs:
            status_emoji = "⏳" if t['status'] == "pending" else "✅" if t['status'] == "approved" else "❌"
            text += f"💵 <b>Amount:</b> ${t['amount']:.2f}\n"
            text += f"🌐 <b>Network:</b> {t['network']}\n"
            text += f"📅 <b>Date:</b> {t['date_time']}\n"
            text += f"📌 <b>Status:</b> {t['status'].upper()} {status_emoji}\n"
            text += f"━━━━━━━━━━━━━━\n"
            
        m = InlineKeyboardMarkup()
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"check_tx_{page-1}", style="primary"))
        if end_idx < len(txs):
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"check_tx_{page+1}", style="primary"))
            
        if nav_buttons:
            m.row(*nav_buttons)
        m.add(InlineKeyboardButton("🏠 Back", callback_data="deposit", style="danger"))
        
        update_msg(text, m)
        
    elif call.data == "add_deposit":
        bot.answer_callback_query(call.id)
        text = "💵 <b>Select Deposit Amount</b>\n\nMinimum deposit is $1."
        m = InlineKeyboardMarkup()
        m.row(
            InlineKeyboardButton("$10", callback_data="dep_amount_10", style="primary"),
            InlineKeyboardButton("$20", callback_data="dep_amount_20", style="primary"),
            InlineKeyboardButton("$50", callback_data="dep_amount_50", style="primary")
        )
        m.add(InlineKeyboardButton("✍️ Custom Amount", callback_data="dep_custom", style="success"))
        m.add(InlineKeyboardButton("🏠 Back", callback_data="deposit", style="danger"))
        update_msg(text, m)
        
    elif call.data.startswith("dep_amount_"):
        bot.answer_callback_query(call.id)
        amount = float(call.data.split("_")[2])
        user_states[call.from_user.id] = {'amount': amount}
        ask_network(call.message.chat.id, call.message.message_id)
        
    elif call.data == "dep_custom":
        bot.answer_callback_query(call.id)
        update_msg("✍️ <b>Enter Custom Amount (Min $1):</b>\n\n<i>Send the amount in chat (e.g. 15.50)</i>", None)
        bot.register_next_step_handler(call.message, process_custom_amount)
        
    elif call.data.startswith("net_"):
        bot.answer_callback_query(call.id)
        network = call.data.replace("net_", "")
        if call.from_user.id not in user_states:
            update_msg("❌ Session expired. Please start over.", get_back_markup())
            return
            
        user_states[call.from_user.id]['network'] = network
        
        details = ""
        qr_path = None
        if network == "BSC BEP 20":
            details = "<b>Address:</b> <code>0xc98b2bcda8694cc4a6726b01ec480eb1a133f316</code>"
            qr_path = "qr_cwallet.png"
        elif network == "C Wallet":
            details = "<b>Address:</b> <code>0x67bf3b2C19e6EE6F4F089A76b51fB12B8b50A534</code>\n<b>ID:</b> <code>62353539</code>"
            qr_path = "qr_bep20.png"
        elif network == "Binance Pay":
            details = "<b>Binance ID:</b> <code>1131825277</code>"
            
        text = (
            f"💰 <b>Payment Details</b>\n\n"
            f"<b>Amount:</b> ${user_states[call.from_user.id]['amount']:.2f}\n"
            f"<b>Network:</b> {network}\n\n"
            f"{details}\n\n"
            f"⚠️ <i>Please send exactly this amount.</i>\n\n"
            f"📸 <b>Send your Transaction ID or Screenshot here to confirm:</b>"
        )
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        m = InlineKeyboardMarkup()
        m.add(InlineKeyboardButton("🏠 Cancel", callback_data="deposit", style="danger"))
        
        if qr_path and os.path.exists(qr_path):
            with open(qr_path, "rb") as qr_img:
                msg = bot.send_photo(call.message.chat.id, qr_img, caption=text, reply_markup=m, parse_mode="HTML")
        else:
            msg = bot.send_message(call.message.chat.id, text, reply_markup=m, parse_mode="HTML")
            
        bot.register_next_step_handler(msg, process_payment_proof)
            
    elif call.data == "profile":
        bot.answer_callback_query(call.id, "Your Profile")
        users = database.get_all_users()
        user_balance = 0.0
        for u in users:
            if u['id'] == call.from_user.id:
                user_balance = u['balance']
                
        role = "Admin" if call.from_user.id in ADMIN_IDS else "User"
        text = f"👤 <b>Profile details for {call.from_user.first_name}</b>\n\n💰 Balance: <b>${user_balance:.2f}</b>\n🔰 Role: {role}"
        
        m = InlineKeyboardMarkup()
        m.add(InlineKeyboardButton("🧾 Check Order History", callback_data="orders", style="primary"))
        m.add(InlineKeyboardButton("📋 Check Payment Transactions", callback_data="check_tx_0", style="success"))
        m.add(InlineKeyboardButton("🏠 Home", callback_data="main_menu", style="danger"))
        
        update_msg(text, m)
        
    elif call.data == "orders":
        bot.answer_callback_query(call.id, "Your Orders")
        orders = database.get_orders_by_user(call.from_user.id)
        if not orders:
            update_msg("🧾 <b>Order History</b>\n\nYou have no recent orders.", get_back_markup())
            return
            
        text = "🧾 <b>Order History</b>\n\n"
        for o in orders:
            text += f"📦 <b>{o['product_title']}</b>\n"
            text += f"📅 <b>Date:</b> {o['date_time']}\n"
            text += f"🛡️ <b>Warranty:</b> {o['warranty']}\n"
            text += f"🔑 <b>Details:</b> <code>{o['account_details']}</code>\n"
            text += "━━━━━━━━━━━━━━\n"
            
        update_msg(text, get_back_markup())
        
    elif call.data == "support":
        bot.answer_callback_query(call.id, "Support Team")
        update_msg("🎧 <b>Contact our support team here:</b> @Meow_7737", get_back_markup())

def ask_network(chat_id, message_id):
    text = "🌐 <b>Select Payment Network</b>"
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("BSC BEP 20", callback_data="net_BSC BEP 20", style="primary"))
    m.add(InlineKeyboardButton("C Wallet", callback_data="net_C Wallet", style="success"))
    m.add(InlineKeyboardButton("Binance Pay", callback_data="net_Binance Pay", style="primary"))
    m.add(InlineKeyboardButton("🏠 Cancel", callback_data="deposit", style="danger"))
    
    try:
        bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, reply_markup=m, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, text, reply_markup=m, parse_mode="HTML")

def process_custom_amount(message):
    try:
        amount = float(message.text.strip())
        if amount < 1:
            msg = bot.send_message(message.chat.id, "⚠️ Minimum deposit is $1. Try again:")
            bot.register_next_step_handler(msg, process_custom_amount)
            return
            
        user_states[message.from_user.id] = {'amount': amount}
        # Send a new message with network selection
        msg = bot.send_message(message.chat.id, "Loading network selection...")
        ask_network(message.chat.id, msg.message_id)
        
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Invalid amount. Please enter numbers only (e.g. 15.50):")
        bot.register_next_step_handler(msg, process_custom_amount)

def process_payment_proof(message):
    user_id = message.from_user.id
    if user_id not in user_states or 'amount' not in user_states[user_id] or 'network' not in user_states[user_id]:
        bot.send_message(message.chat.id, "❌ Session expired. Please start over from /start.")
        return
        
    amount = user_states[user_id]['amount']
    network = user_states[user_id]['network']
    
    # Validate: only photo or alphanumeric text allowed
    is_valid = False
    if message.photo:
        is_valid = True
        tx_id = "Screenshot Provided"
    elif message.text and message.text.isalnum():
        is_valid = True
        tx_id = message.text
        
    if not is_valid:
        if user_id in user_states:
            del user_states[user_id]
        bot.send_message(message.chat.id, "❌ <b>Invalid Proof!</b>\nOnly screenshots or alphanumeric transaction IDs are accepted. Deposit cancelled.", parse_mode="HTML")
        # Pop up new welcome message
        text, markup = get_main_menu(message.from_user)
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
        return
    
    # Save to db
    database.add_transaction(user_id, amount, network, tx_id)
    
    text = (
        "✅ <b>Payment Details Submitted!</b>\n\n"
        "Your transaction is now pending admin approval. You will be notified once it is approved."
    )
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("🏠 Home", callback_data="main_menu", style="danger"))
    bot.send_message(message.chat.id, text, reply_markup=m, parse_mode="HTML")
    
    # Send admin alert here via Telegram directly so they see the screenshot
    for admin_id in ADMIN_IDS:
        try:
            admin_text = f"🔔 <b>NEW DEPOSIT PENDING</b>\n\n👤 <b>User ID:</b> <code>{user_id}</code>\n💵 <b>Amount:</b> ${amount:.2f}\n🌐 <b>Network:</b> {network}\n\n<i>Approve or decline via the Web Admin Panel.</i>"
            if message.photo:
                bot.send_photo(admin_id, message.photo[-1].file_id, caption=admin_text, parse_mode="HTML")
            else:
                admin_text += f"\n\n📝 <b>TxID Provided:</b> <code>{tx_id}</code>"
                bot.send_message(admin_id, admin_text, parse_mode="HTML")
        except:
            pass # Ignore if admin blocked the bot
            
    del user_states[user_id]

def expiry_checker_loop():
    import time
    while True:
        try:
            orders = database.get_all_orders()
            now = datetime.now()
            for o in orders:
                if o.get('duration_ends_at') and not o.get('duration_notified'):
                    ends_at = datetime.fromisoformat(o['duration_ends_at'])
                    if ends_at - timedelta(days=1) <= now:
                        try:
                            title = o.get('product_title') or "your product"
                            bot.send_message(o['user_id'], f"⚠️ <b>Reminder!</b>\n\nYour access for <b>{title}</b> will expire in 1 day (on {ends_at.strftime('%Y-%m-%d')}).", parse_mode="HTML")
                            database.mark_order_notified(o['id'], 'duration')
                        except:
                            pass
                
                if o.get('warranty_ends_at') and not o.get('warranty_notified'):
                    ends_at = datetime.fromisoformat(o['warranty_ends_at'])
                    if ends_at - timedelta(days=1) <= now:
                        try:
                            title = o.get('product_title') or "your product"
                            bot.send_message(o['user_id'], f"⚠️ <b>Reminder!</b>\n\nYour warranty for <b>{title}</b> will expire in 1 day (on {ends_at.strftime('%Y-%m-%d')}).", parse_mode="HTML")
                            database.mark_order_notified(o['id'], 'warranty')
                        except:
                            pass
        except Exception as e:
            print("Expiry Checker Error:", e)
            
        time.sleep(21600) # Check every 6 hours

if __name__ == "__main__":
    print("Bot is running...")
    import threading
    t = threading.Thread(target=expiry_checker_loop, daemon=True)
    t.start()
    bot.infinity_polling()
