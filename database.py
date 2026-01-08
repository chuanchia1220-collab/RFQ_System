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
    # Added materials, forms, qualifications as TEXT columns
    # Note: If table exists without these columns, this CREATE IF NOT EXISTS won't add them.
    # In a real app, we would use migrations. For this local dev, we assume fresh DB or manual reset.
    # To be safe for this "skeleton" phase, I'll attempt to add columns if they don't exist, or just recreate.
    # Simpler: just ensure the schema definition is correct.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact_person TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        materials TEXT,
        forms TEXT,
        qualifications TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Quick fix to ensure columns exist if table already existed (for dev convenience)
    try:
        cursor.execute("ALTER TABLE suppliers ADD COLUMN materials TEXT")
    except sqlite3.OperationalError:
        pass # Column likely exists
    try:
        cursor.execute("ALTER TABLE suppliers ADD COLUMN forms TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE suppliers ADD COLUMN qualifications TEXT")
    except sqlite3.OperationalError:
        pass

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
def add_supplier(name, contact_person, email, phone, address, materials, forms, qualifications):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO suppliers (name, contact_person, email, phone, address, materials, forms, qualifications)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, contact_person, email, phone, address, materials, forms, qualifications))
    conn.commit()
    conn.close()

def get_suppliers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM suppliers')
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_supplier(supplier_id, name, contact_person, email, phone, address, materials, forms, qualifications):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE suppliers
        SET name = ?, contact_person = ?, email = ?, phone = ?, address = ?, 
            materials = ?, forms = ?, qualifications = ?
        WHERE id = ?
    ''', (name, contact_person, email, phone, address, materials, forms, qualifications, supplier_id))
    conn.commit()
    conn.close()

def delete_supplier(supplier_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM suppliers WHERE id = ?', (supplier_id,))
    conn.commit()
    conn.close()

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

def search_suppliers(materials_list, forms_list):
    """
    Searches for suppliers that match at least one material OR one form.
    Args:
        materials_list (list): List of material strings.
        forms_list (list): List of form strings.
    Returns:
        list: List of matching supplier rows.
    """
    import json

    all_suppliers = get_suppliers()
    matched_suppliers = []

    target_materials = set(materials_list)
    target_forms = set(forms_list)

    for supplier in all_suppliers:
        # Supplier columns: id, name, contact, email, phone, address, materials, forms, ...
        # indexes: 0, 1, 2, 3, 4, 5, 6, 7
        try:
            s_materials = set(json.loads(supplier[6])) if supplier[6] else set()
            s_forms = set(json.loads(supplier[7])) if supplier[7] else set()

            # Check for intersection
            mat_match = not s_materials.isdisjoint(target_materials)
            form_match = not s_forms.isdisjoint(target_forms)

            if mat_match or form_match:
                matched_suppliers.append(supplier)

        except json.JSONDecodeError:
            continue

    return matched_suppliers

if __name__ == "__main__":
    init_db()
