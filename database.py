import sqlite3
from contextlib import closing

DB_FILE = 'revox.db'

def init_db():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with closing(conn.cursor()) as cursor:
            # Users Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    balance REAL DEFAULT 0.0,
                    role TEXT DEFAULT 'user'
                )
            ''')
            # Products Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    info TEXT,
                    image_url TEXT,
                    price REAL NOT NULL
                )
            ''')
            # Stock Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    credentials TEXT NOT NULL,
                    is_sold INTEGER DEFAULT 0,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            # Transactions Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    network TEXT,
                    tx_id TEXT,
                    date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            # Orders Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    account_details TEXT NOT NULL,
                    date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    warranty TEXT,
                    duration_ends_at TEXT,
                    warranty_ends_at TEXT,
                    duration_notified INTEGER DEFAULT 0,
                    warranty_notified INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
            
            # Migrations for existing tables
            try:
                cursor.execute("ALTER TABLE products ADD COLUMN has_warranty INTEGER DEFAULT 0")
                cursor.execute("ALTER TABLE products ADD COLUMN duration_days INTEGER DEFAULT 0")
                cursor.execute("ALTER TABLE products ADD COLUMN warranty_days INTEGER DEFAULT 0")
                cursor.execute("ALTER TABLE orders ADD COLUMN duration_ends_at TEXT")
                cursor.execute("ALTER TABLE orders ADD COLUMN warranty_ends_at TEXT")
                cursor.execute("ALTER TABLE orders ADD COLUMN duration_notified INTEGER DEFAULT 0")
                cursor.execute("ALTER TABLE orders ADD COLUMN warranty_notified INTEGER DEFAULT 0")
                conn.commit()
            except:
                pass

# Product functions
def get_products():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute('''
                SELECT p.*, (SELECT COUNT(*) FROM stock WHERE product_id = p.id AND is_sold = 0) as stock_count 
                FROM products p
            ''')
            return [dict(row) for row in cursor.fetchall()]

def add_product(title, info, image_url, price, has_warranty=0, duration_days=0, warranty_days=0):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('INSERT INTO products (title, info, image_url, price, has_warranty, duration_days, warranty_days) VALUES (?, ?, ?, ?, ?, ?, ?)', (title, info, image_url, price, has_warranty, duration_days, warranty_days))
            conn.commit()

def delete_product(product_id):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('DELETE FROM stock WHERE product_id = ?', (product_id,))
            cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
            conn.commit()

def get_product_by_id(product_id):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT p.*, (SELECT COUNT(*) FROM stock WHERE product_id = p.id AND is_sold = 0) as stock_count FROM products p WHERE id = ?', (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

# Stock functions
def add_stock(product_id, credentials):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with closing(conn.cursor()) as cursor:
            lines = credentials.strip().split('\n')
            for line in lines:
                if line.strip():
                    cursor.execute('INSERT INTO stock (product_id, credentials) VALUES (?, ?)', (product_id, line.strip()))
            conn.commit()

def get_stock_by_product(product_id):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT * FROM stock WHERE product_id = ? AND is_sold = 0', (product_id,))
            return [dict(row) for row in cursor.fetchall()]

def delete_stock(stock_id):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('DELETE FROM stock WHERE id = ?', (stock_id,))
            conn.commit()

def get_unsold_stock(product_id):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT * FROM stock WHERE product_id = ? AND is_sold = 0 LIMIT 1', (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

def mark_stock_sold(stock_id):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('UPDATE stock SET is_sold = 1 WHERE id = ?', (stock_id,))
            conn.commit()

# User functions
def update_user_balance(user_id, amount, username="Unknown"):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                new_balance = row[0] + amount
                cursor.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user_id))
            else:
                cursor.execute('INSERT INTO users (id, username, balance) VALUES (?, ?, ?)', (user_id, username, amount))
            conn.commit()

def get_all_users():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT * FROM users')
            return [dict(row) for row in cursor.fetchall()]

# Transaction Functions
def add_transaction(user_id, amount, network, tx_id):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('INSERT INTO transactions (user_id, amount, network, tx_id) VALUES (?, ?, ?, ?)', (user_id, amount, network, tx_id))
            conn.commit()

def get_transactions_by_user(user_id):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT * FROM transactions WHERE user_id = ? ORDER BY date_time DESC', (user_id,))
            return [dict(row) for row in cursor.fetchall()]

def get_pending_transactions():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT * FROM transactions WHERE status = "pending" ORDER BY date_time DESC')
            return [dict(row) for row in cursor.fetchall()]

def update_transaction_status(tx_id, status):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute('UPDATE transactions SET status = ? WHERE id = ?', (status, tx_id))
            cursor.execute('SELECT * FROM transactions WHERE id = ?', (tx_id,))
            tx = cursor.fetchone()
            conn.commit()
            
            if tx and status == 'approved':
                # Re-use the proper function so it handles new users correctly
                update_user_balance(tx['user_id'], tx['amount'])
                
            return dict(tx) if tx else None

# Order Functions
def get_orders_by_user(user_id):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT o.*, p.title as product_title FROM orders o JOIN products p ON o.product_id = p.id WHERE o.user_id = ? ORDER BY o.date_time DESC', (user_id,))
            return [dict(row) for row in cursor.fetchall()]

def get_all_orders():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT o.*, p.title as product_title FROM orders o LEFT JOIN products p ON o.product_id = p.id')
            return [dict(row) for row in cursor.fetchall()]

def create_order(user_id, product_id, account_details, warranty_text, duration_ends_at, warranty_ends_at):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('''
                INSERT INTO orders (user_id, product_id, account_details, warranty, duration_ends_at, warranty_ends_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, product_id, account_details, warranty_text, duration_ends_at, warranty_ends_at))
            conn.commit()

def mark_order_notified(order_id, type_str):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(f'UPDATE orders SET {type_str}_notified = 1 WHERE id = ?', (order_id,))
            conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
