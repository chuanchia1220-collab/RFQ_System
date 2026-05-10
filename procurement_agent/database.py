import sqlite3
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("system.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

DB_NAME = "Supplier_Docs.db"

def get_connection():
    """Returns a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
        return conn
    except Exception as e:
        logging.error("Failed to connect to database", exc_info=True)
        raise

def init_db():
    """Initializes the database schema with Supplier_Master and Document_Master tables."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Supplier Master Table
        # Note: pmn31 column kept for future TIPTOP ERP integration flexibility
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Supplier_Master (
                Supplier_ID TEXT PRIMARY KEY,
                Name TEXT NOT NULL,
                Email TEXT,
                pmn31 TEXT
            )
        ''')

        # Document Master Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Document_Master (
                Doc_ID TEXT PRIMARY KEY,
                Supplier_ID TEXT NOT NULL,
                Doc_Type TEXT NOT NULL,
                File_Path TEXT,
                Status TEXT NOT NULL CHECK(Status IN ('signed', 'pending', '已簽回')),
                FOREIGN KEY (Supplier_ID) REFERENCES Supplier_Master(Supplier_ID)
            )
        ''')

        # Lossless Schema Upgrade
        # Check and add Tax_ID, Category_Code, Category_Name if not exist
        cursor.execute("PRAGMA table_info(Supplier_Master)")
        columns = [info[1] for info in cursor.fetchall()]

        if 'Tax_ID' not in columns:
            cursor.execute("ALTER TABLE Supplier_Master ADD COLUMN Tax_ID TEXT")
        if 'Category_Code' not in columns:
            cursor.execute("ALTER TABLE Supplier_Master ADD COLUMN Category_Code TEXT")
        if 'Category_Name' not in columns:
            cursor.execute("ALTER TABLE Supplier_Master ADD COLUMN Category_Name TEXT")

        conn.commit()
        logging.info("Database initialized and migrated successfully.")
    except Exception as e:
        logging.error("Error initializing database schema", exc_info=True)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Executes a SELECT query and returns the results as a list of dicts."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logging.error(f"Error executing query: {query}", exc_info=True)
        return []
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def execute_update(query: str, params: tuple = ()):
    """Executes an INSERT, UPDATE, or DELETE query."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
    except Exception as e:
        logging.error(f"Error executing update: {query}", exc_info=True)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def update_document_status(supplier_id: str, doc_type: str, file_path: str, status: str = '已簽回'):
    """Updates the status and file path of a document."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if the document exists
        cursor.execute("SELECT Doc_ID FROM Document_Master WHERE Supplier_ID = ? AND Doc_Type = ?", (supplier_id, doc_type))
        row = cursor.fetchone()

        if row:
            cursor.execute('''
                UPDATE Document_Master
                SET Status = ?, File_Path = ?
                WHERE Supplier_ID = ? AND Doc_Type = ?
            ''', (status, file_path, supplier_id, doc_type))
        else:
            import uuid
            doc_id = "DOC-" + str(uuid.uuid4())[:8]
            cursor.execute('''
                INSERT INTO Document_Master (Doc_ID, Supplier_ID, Doc_Type, File_Path, Status)
                VALUES (?, ?, ?, ?, ?)
            ''', (doc_id, supplier_id, doc_type, file_path, status))

        conn.commit()
    except Exception as e:
        logging.error(f"Error updating document status for {supplier_id} - {doc_type}", exc_info=True)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def upsert_suppliers(supplier_data_list: List[Dict[str, Any]]):
    """Upserts suppliers based on Name and Tax_ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # We need to know which columns are in Supplier_Master to avoid errors
        # on missing Address, Materials, Forms, Qualifications
        cursor.execute("PRAGMA table_info(Supplier_Master)")
        db_columns = [info[1] for info in cursor.fetchall()]

        for data in supplier_data_list:
            name = data.get("Name", "")
            tax_id = data.get("Tax_ID", "")

            # Use Name and Tax_ID to identify a supplier
            # If both Name and Tax_ID match, it is an existing supplier.
            # (Assuming matching by just Name if Tax_ID is empty is also valid, or Name + Tax_ID combined)
            cursor.execute(
                "SELECT * FROM Supplier_Master WHERE Name = ? AND (Tax_ID = ? OR Tax_ID IS NULL)",
                (name, tax_id)
            )
            existing = cursor.fetchone()

            if existing:
                existing_dict = dict(existing)

                # Merge logic
                new_contact = data.get("Contact", "")
                old_contact = existing_dict.get("pmn31", "")
                merged_contact = "; ".join(filter(None, [old_contact, new_contact])) if new_contact != old_contact else old_contact

                new_email = data.get("Email", "")
                old_email = existing_dict.get("Email", "")
                merged_email = "; ".join(filter(None, [old_email, new_email])) if new_email != old_email else old_email

                cat_code = data.get("Category_Code", existing_dict.get("Category_Code", ""))
                cat_name = data.get("Category_Name", existing_dict.get("Category_Name", ""))

                update_query = '''
                    UPDATE Supplier_Master
                    SET pmn31 = ?, Email = ?, Category_Code = ?, Category_Name = ?
                '''
                params = [merged_contact, merged_email, cat_code, cat_name]

                # Update Address only if the column exists in db
                if 'Address' in db_columns:
                    update_query += ", Address = ?"
                    params.append(data.get("Address", existing_dict.get("Address", "")))

                update_query += " WHERE Supplier_ID = ?"
                params.append(existing_dict["Supplier_ID"])

                cursor.execute(update_query, tuple(params))
            else:
                import uuid
                supplier_id = data.get("Supplier_ID")
                if not supplier_id:
                    supplier_id = "TMP-" + str(uuid.uuid4())[:8]

                insert_cols = ["Supplier_ID", "Name", "Tax_ID", "Email", "pmn31", "Category_Code", "Category_Name"]
                insert_vals = [
                    supplier_id,
                    name,
                    tax_id,
                    data.get("Email", ""),
                    data.get("Contact", ""),
                    data.get("Category_Code", ""),
                    data.get("Category_Name", "")
                ]

                if 'Address' in db_columns:
                    insert_cols.append("Address")
                    insert_vals.append(data.get("Address", ""))

                if 'Materials' in db_columns:
                    insert_cols.append("Materials")
                    insert_vals.append(data.get("Materials", ""))
                if 'Forms' in db_columns:
                    insert_cols.append("Forms")
                    insert_vals.append(data.get("Forms", ""))
                if 'Qualifications' in db_columns:
                    insert_cols.append("Qualifications")
                    insert_vals.append(data.get("Qualifications", ""))

                placeholders = ", ".join(["?"] * len(insert_cols))
                col_str = ", ".join(insert_cols)

                cursor.execute(
                    f"INSERT INTO Supplier_Master ({col_str}) VALUES ({placeholders})",
                    tuple(insert_vals)
                )

        conn.commit()
    except Exception as e:
        logging.error("Error upserting suppliers", exc_info=True)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def seed_dummy_data():
    """Dummy function to prevent error when app.py calls it. Keep empty or add logic later."""
    pass

# --- Helper Functions for UI ---

def get_suppliers() -> List[Dict[str, Any]]:
    """Retrieves all suppliers."""
    return execute_query("SELECT * FROM Supplier_Master")

def get_documents_by_supplier(supplier_id: str = None) -> List[Dict[str, Any]]:
    """Retrieves documents, optionally filtered by supplier."""
    if supplier_id:
        return execute_query(
            "SELECT d.*, s.Name as Supplier_Name FROM Document_Master d JOIN Supplier_Master s ON d.Supplier_ID = s.Supplier_ID WHERE d.Supplier_ID = ?",
            (supplier_id,)
        )
    else:
        return execute_query("SELECT d.*, s.Name as Supplier_Name FROM Document_Master d JOIN Supplier_Master s ON d.Supplier_ID = s.Supplier_ID")

def get_all_document_statuses() -> List[Dict[str, Any]]:
    """Retrieves all documents with their supplier names."""
    query = '''
        SELECT
            d.Doc_ID,
            s.Supplier_ID,
            s.Name as Supplier_Name,
            d.Doc_Type,
            d.Status
        FROM
            Document_Master d
        JOIN
            Supplier_Master s ON d.Supplier_ID = s.Supplier_ID
    '''
    return execute_query(query)

def get_missing_documents() -> List[Dict[str, Any]]:
    """Retrieves a list of suppliers and the documents they are missing (Status = 'pending')."""
    query = '''
        SELECT
            s.Supplier_ID,
            s.Name,
            s.Email,
            GROUP_CONCAT(d.Doc_Type, ', ') as Missing_Docs
        FROM
            Supplier_Master s
        JOIN
            Document_Master d ON s.Supplier_ID = d.Supplier_ID
        WHERE
            d.Status = 'pending'
        GROUP BY
            s.Supplier_ID
    '''
    return execute_query(query)

def get_missing_documents_by_supplier(supplier_ids: List[str]) -> List[Dict[str, Any]]:
    """Retrieves missing documents for specific suppliers."""
    if not supplier_ids:
        return []

    placeholders = ','.join(['?'] * len(supplier_ids))
    query = f'''
        SELECT
            s.Supplier_ID,
            s.Name,
            s.Email,
            d.Doc_Type,
            d.Doc_ID
        FROM
            Supplier_Master s
        JOIN
            Document_Master d ON s.Supplier_ID = d.Supplier_ID
        WHERE
            d.Status = 'pending' AND s.Supplier_ID IN ({placeholders})
    '''
    return execute_query(query, tuple(supplier_ids))


def import_csv_data():
    """Imports real data from suppliers.csv."""
    import os, csv

    csv_path = "suppliers.csv"
    if not os.path.exists(csv_path) and os.path.exists("../suppliers.csv"):
        csv_path = "../suppliers.csv"

    if not os.path.exists(csv_path):
        logging.info(f"{csv_path} not found, skipping import.")
        return

    try:
        # Check if data already exists
        if execute_query("SELECT COUNT(*) as count FROM Supplier_Master")[0]['count'] > 0:
            return

        with open(csv_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for idx, row in enumerate(reader):
                supplier_id = f"V{idx+1:03}"
                execute_update(
                    "INSERT INTO Supplier_Master (Supplier_ID, Name, Email, pmn31) VALUES (?, ?, ?, ?)",
                    (supplier_id, row.get('Name'), row.get('Email'), row.get('Contact'))
                )
        logging.info("CSV data imported successfully.")
    except Exception as e:
        logging.error("Failed to import CSV data", exc_info=True)

if __name__ == "__main__":
    init_db()
    import_csv_data()
