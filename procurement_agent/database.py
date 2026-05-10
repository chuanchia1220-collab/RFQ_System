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

        conn.commit()
        logging.info("Database initialized successfully.")
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
    query = '''
        UPDATE Document_Master
        SET Status = ?, File_Path = ?
        WHERE Supplier_ID = ? AND Doc_Type = ?
    '''
    execute_update(query, (status, file_path, supplier_id, doc_type))

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
