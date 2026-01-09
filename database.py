# database.py
# Section 4: Schema

import sqlite3
import json

DB_NAME = "rfq_system.db"
_connection = None

def get_connection():
    global _connection
    if DB_NAME == ":memory:":
        if _connection is None:
            _connection = sqlite3.connect(DB_NAME, check_same_thread=False)
        return _connection
    return sqlite3.connect(DB_NAME)

def init_db():
    """Initializes the database with schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table: Suppliers (Section 4.1)
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
    
    # Ensure columns exist (for existing DB compatibility)
    for col in ["materials", "forms", "qualifications"]:
        try:
            cursor.execute(f"ALTER TABLE suppliers ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass

    # Table: RFQ Templates (Section 4.2)
    # Using TEXT for JSON/Array fields
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        subject_format TEXT,
        preamble_html TEXT,
        closing_html TEXT,
        table_fields TEXT,
        font_family TEXT,
        font_size INTEGER,
        table_styles TEXT,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Ensure columns exist for templates if table exists with old schema
    template_cols = {
        "subject_format": "TEXT",
        "preamble_html": "TEXT",
        "closing_html": "TEXT",
        "table_fields": "TEXT",
        "font_family": "TEXT",
        "font_size": "INTEGER",
        "table_styles": "TEXT",
        "created_by": "TEXT",
        "cc_recipients": "TEXT",       # 新增: 副本欄位
        "use_default_subject": "INTEGER" # 新增: 是否使用預設主旨 (0 or 1)
    }
    for col, dtype in template_cols.items():
        try:
            cursor.execute(f"ALTER TABLE templates ADD COLUMN {col} {dtype}")
        except sqlite3.OperationalError:
            pass

    # Table: RFQ Requests (Section 4.3)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rfq_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_text TEXT,
        parsed_items TEXT,
        created_by TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Table: RFQ Items (Section 4.4)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rfq_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER,
        item_index INTEGER,
        material_type TEXT,
        form_type TEXT,
        spec TEXT,
        matched_suppliers TEXT,
        selected_supplier INTEGER,
        email_payload TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (request_id) REFERENCES rfq_requests(id)
    )
    ''')

    if DB_NAME != ":memory:":
        conn.close()

# --- CRUD Operations for Suppliers ---

def add_supplier(name, contact_person, email, phone, address, materials, forms, qualifications):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO suppliers (name, contact_person, email, phone, address, materials, forms, qualifications)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, contact_person, email, phone, address, materials, forms, qualifications))
    conn.commit()
    if DB_NAME != ":memory:":
        conn.close()

def get_suppliers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM suppliers')
    rows = cursor.fetchall()
    if DB_NAME != ":memory:":
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
    if DB_NAME != ":memory:":
        conn.close()

def delete_supplier(supplier_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM suppliers WHERE id = ?', (supplier_id,))
    conn.commit()
    if DB_NAME != ":memory:":
        conn.close()

# --- CRUD Operations for Templates ---

# Updated to include cc_recipients and use_default_subject
def add_template(name, subject_format, preamble_html, closing_html, cc_recipients="", use_default_subject=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO templates (name, subject_format, preamble_html, closing_html, cc_recipients, use_default_subject)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, subject_format, preamble_html, closing_html, cc_recipients, use_default_subject))
    conn.commit()
    if DB_NAME != ":memory:":
        conn.close()

def update_template(template_id, name, subject_format, preamble_html, closing_html, cc_recipients, use_default_subject):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE templates
        SET name = ?, subject_format = ?, preamble_html = ?, closing_html = ?, cc_recipients = ?, use_default_subject = ?
        WHERE id = ?
    ''', (name, subject_format, preamble_html, closing_html, cc_recipients, use_default_subject, template_id))
    conn.commit()
    if DB_NAME != ":memory:":
        conn.close()

def delete_template(template_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM templates WHERE id = ?', (template_id,))
    conn.commit()
    if DB_NAME != ":memory:":
        conn.close()

def get_templates():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM templates')
    rows = cursor.fetchall()
    if DB_NAME != ":memory:":
        conn.close()
    return rows

# --- RFQ Operations --- (Unchanged)

def save_rfq_request(raw_text, parsed_items_json, created_by="system"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO rfq_requests (raw_text, parsed_items, created_by, status)
        VALUES (?, ?, ?, 'Analyzed')
    ''', (raw_text, parsed_items_json, created_by))
    req_id = cursor.lastrowid
    conn.commit()
    if DB_NAME != ":memory:":
        conn.close()
    return req_id

def save_rfq_item(request_id, item_index, material_type, form_type, spec_json, matched_suppliers_ids):
    conn = get_connection()
    cursor = conn.cursor()
    matched_suppliers_json = json.dumps(matched_suppliers_ids)
    cursor.execute('''
        INSERT INTO rfq_items (request_id, item_index, material_type, form_type, spec, matched_suppliers, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    ''', (request_id, item_index, material_type, form_type, spec_json, matched_suppliers_json))
    conn.commit()
    if DB_NAME != ":memory:":
        conn.close()

def search_suppliers(materials_list, forms_list):
    conn = get_connection()
    cursor = conn.cursor()
    all_suppliers = get_suppliers()
    matched_suppliers = []

    target_materials = set(materials_list)
    target_forms = set(forms_list)

    for supplier in all_suppliers:
        try:
            s_materials = set(json.loads(supplier[6])) if supplier[6] else set()
            s_forms = set(json.loads(supplier[7])) if supplier[7] else set()
            mat_match = not s_materials.isdisjoint(target_materials)
            form_match = not s_forms.isdisjoint(target_forms)
            if mat_match or form_match:
                matched_suppliers.append(supplier)
        except json.JSONDecodeError:
            continue

    conditions = []
    params = []
    if materials_list:
        mat_conditions = []
        for m in materials_list:
            mat_conditions.append("materials LIKE ?")
            params.append(f'%"{m}"%')
        if mat_conditions:
            conditions.append(f"({' OR '.join(mat_conditions)})")

    if forms_list:
        form_conditions = []
        for f in forms_list:
            form_conditions.append("forms LIKE ?")
            params.append(f'%"{f}"%')
        if form_conditions:
            conditions.append(f"({' OR '.join(form_conditions)})")

    if not conditions:
        return []

    sql = f"SELECT * FROM suppliers WHERE {' OR '.join(conditions)}"
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
