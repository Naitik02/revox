from flask import Flask, render_template, request, redirect, url_for, flash
import database
import telebot

app = Flask(__name__)
app.secret_key = 'supersecretrevoxkey'

# Bot instance for broadcasting
BOT_TOKEN = "8989409928:AAGLBtV23Jleyn7BQr3AL3PV3Cw8VwNDLpA"
bot = telebot.TeleBot(BOT_TOKEN)

# Ensure DB is initialized when web starts
database.init_db()

@app.route('/')
def admin_panel():
    products = database.get_products()
    users = database.get_all_users()
    pending_txs = database.get_pending_transactions()
    
    # Create a mapping of user_id to username
    user_map = {u['id']: u.get('username', 'Unknown') for u in users}
    
    # Fetch stock details for each product
    all_stock = {p['id']: database.get_stock_by_product(p['id']) for p in products}
    
    total_users = len(users)
    total_products = len(products)
    
    return render_template('admin.html', products=products, users=users, pending_txs=pending_txs, user_map=user_map, total_users=total_users, total_products=total_products, all_stock=all_stock)

@app.route('/add_product', methods=['POST'])
def add_product():
    title = request.form.get('title')
    info = request.form.get('info')
    image_url = request.form.get('image_url')
    price = request.form.get('price')
    has_warranty = 1 if request.form.get('has_warranty') == 'on' else 0
    duration_days = int(request.form.get('duration_days') or 0)
    warranty_days = int(request.form.get('warranty_days') or 0)
    
    if title and price:
        database.add_product(title, info, image_url, float(price), has_warranty, duration_days, warranty_days)
        flash("Product added successfully!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    database.delete_product(product_id)
    flash("Product deleted successfully!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/delete_stock/<int:stock_id>', methods=['POST'])
def delete_stock(stock_id):
    database.delete_stock(stock_id)
    flash("Stock removed successfully!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/add_stock', methods=['POST'])
def add_stock():
    product_id = request.form.get('product_id')
    ids = request.form.getlist('ids[]')
    passes = request.form.getlist('passes[]')
    
    if product_id and ids and passes:
        for i in range(len(ids)):
            if ids[i].strip():
                # Add to DB combining them with a colon
                database.add_stock(int(product_id), f"{ids[i].strip()}:{passes[i].strip()}")
        flash("Stock added successfully!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/update_balance', methods=['POST'])
def update_balance():
    user_id = request.form.get('user_id')
    amount = request.form.get('amount')
    
    if user_id and amount:
        database.update_user_balance(int(user_id), float(amount))
        flash("Balance updated successfully!", "success")
    return redirect(url_for('admin_panel'))

import threading

def bg_broadcast(users, message, file_data, file_name):
    sent_count = 0
    file_id = None
    for user in users:
        try:
            if file_data:
                if not file_id:
                    # Upload once to the first user
                    msg = bot.send_photo(user['id'], file_data, caption=message)
                    file_id = msg.photo[-1].file_id
                else:
                    # Reuse file_id for others
                    bot.send_photo(user['id'], file_id, caption=message)
            else:
                bot.send_message(user['id'], message)
            sent_count += 1
        except Exception as e:
            print(f"Failed to send to {user['id']}: {e}")
    print(f"Broadcast finished. Sent to {sent_count} users.")

@app.route('/broadcast', methods=['POST'])
def broadcast():
    message = request.form.get('message')
    file = request.files.get('attachment')
    
    if message or (file and file.filename):
        users = database.get_all_users()
        file_data = file.read() if (file and file.filename) else None
        file_name = file.filename if (file and file.filename) else None
        
        t = threading.Thread(target=bg_broadcast, args=(users, message, file_data, file_name))
        t.start()
        
        flash(f"Broadcast started in the background for {len(users)} users!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/approve_tx/<int:tx_id>', methods=['POST'])
def approve_tx(tx_id):
    tx = database.update_transaction_status(tx_id, 'approved')
    if tx:
        try:
            bot.send_message(tx['user_id'], f"✅ <b>Payment Approved!</b>\n\nYour deposit of <b>${tx['amount']:.2f}</b> has been credited to your balance.\n\n🎧 If any queries, then Contact : @Meow_7737", parse_mode="HTML")
        except Exception as e:
            print("Failed to notify user:", e)
    flash(f"Transaction {tx_id} approved and balance updated!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/decline_tx/<int:tx_id>', methods=['POST'])
def decline_tx(tx_id):
    tx = database.update_transaction_status(tx_id, 'declined')
    if tx:
        try:
            bot.send_message(tx['user_id'], f"❌ <b>Payment Declined!</b>\n\nYour deposit of <b>${tx['amount']:.2f}</b> was declined.\n\n🎧 If any queries, then Contact : @Meow_7737", parse_mode="HTML")
        except Exception as e:
            print("Failed to notify user:", e)
    flash(f"Transaction {tx_id} declined.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/get_image/<file_id>')
def get_image(file_id):
    import io
    from flask import send_file
    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        return send_file(io.BytesIO(downloaded_file), mimetype='image/jpeg')
    except Exception as e:
        return "Image not found", 404

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
