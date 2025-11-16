# models/database.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "fastfood.db"


def get_connection():
    # allow threads, wait longer before giving up, enable WAL for better concurrency
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Categories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)

    # Products
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER,
        price REAL NOT NULL,
        image TEXT,
        cost REAL DEFAULT 0.0,
        status TEXT DEFAULT 'available',
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )
    """)

    # Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        area TEXT
    )
    """)

    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'cashier', 'kitchen', 'manager'))
    )
    """)


    # Orders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id INTEGER,
        user_id INTEGER,
        total REAL,
        payment_type TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (table_id) REFERENCES tables(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Order Items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price REAL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
      # Add printers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS printers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            connection_type TEXT CHECK(connection_type IN ('usb', 'network')),
            vendor_id TEXT,
            product_id TEXT,
            serial_number TEXT,
            ip_address TEXT,
            port INTEGER,
            assigned_categories TEXT,
            status TEXT DEFAULT 'offline'
        );

    """)
    

     # Add settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_name TEXT,
            address TEXT,
            phone TEXT,
            logo_path TEXT,
            vat_percentage REAL DEFAULT 0,
            currency_symbol TEXT DEFAULT 'DZD',
            inventory_enabled INTEGER DEFAULT 0
        )
    """)
     # Add inventory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity REAL DEFAULT 0,
            unit TEXT DEFAULT 'pcs',
            min_quantity REAL DEFAULT 0,
            cost REAL DEFAULT 0,
            product_id INTEGER,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )


    """)


    # Ensure one default row exists
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO settings (restaurant_name, address, phone, logo_path, vat_percentage, currency_symbol, inventory_enabled)
        VALUES ('My Restaurant', '123 Main St', '0550 000 000', '', 0, 'DZD', 0)
        """)



    
    conn.commit()
    conn.close()
