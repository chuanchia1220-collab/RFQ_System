# database.py
# Section 4: Schema

import sqlite3

DB_NAME = "rfq_system.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    """Initializes the database with schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table: Suppliers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact_person TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Table: RFQ Templates
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Table: RFQs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rfqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER,
        status TEXT DEFAULT 'New',
        request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        details TEXT,
        FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
    )
    ''')

    conn.commit()
    conn.close()

# CRUD Operations for Suppliers
def add_supplier(name, contact_person, email, phone, address):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO suppliers (name, contact_person, email, phone, address)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, contact_person, email, phone, address))
    conn.commit()
    conn.close()

def get_suppliers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM suppliers')
    rows = cursor.fetchall()
    conn.close()
    return rows

# CRUD Operations for Templates
def add_template(name, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO templates (name, content)
        VALUES (?, ?)
    ''', (name, content))
    conn.commit()
    conn.close()

def get_templates():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM templates')
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
