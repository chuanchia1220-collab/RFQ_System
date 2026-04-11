import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional

DB_NAME = "database.db"

class DBManager:
    """
    資料庫封裝模組，負責管理 SQLite 連線與資料表操作。
    """
    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """取得資料庫連線"""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """初始化資料表結構 (相容既有 database.db，絕對不使用 DROP TABLE)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 建立 Item_Master 資料表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Item_Master (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_spec TEXT NOT NULL,
                        material_type TEXT,
                        form_type TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 建立 Supplier_List 資料表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Supplier_List (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        materials TEXT,
                        forms TEXT,
                        qualifications TEXT,
                        contact_email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 建立 RFQ_History 資料表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS RFQ_History (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rfq_id TEXT UNIQUE NOT NULL,
                        raw_data TEXT,
                        parsed_data TEXT,
                        status TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logging.info("Database tables initialized successfully.")
        except sqlite3.Error as e:
            logging.error(f"Error initializing database: {e}")

    def get_suppliers_for_item(self, item_spec: str) -> List[Dict[str, Any]]:
        """模糊比對料號或規格，回傳建議供應商清單"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 使用簡單的 LIKE 進行模糊比對 (針對規格、材料或形狀)
                query = '''
                    SELECT * FROM Supplier_List
                    WHERE materials LIKE ? OR forms LIKE ?
                '''
                search_term = f"%{item_spec}%"
                cursor.execute(query, (search_term, search_term))
                rows = cursor.fetchall()

                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"Error fetching suppliers for item '{item_spec}': {e}")
            return []

    def save_rfq_record(self, rfq_id: str, raw_data: str, parsed_data: dict, status: str = "PENDING") -> bool:
        """儲存詢價歷程"""
        try:
            parsed_data_str = json.dumps(parsed_data, ensure_ascii=False)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO RFQ_History (rfq_id, raw_data, parsed_data, status)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(rfq_id) DO UPDATE SET
                        raw_data=excluded.raw_data,
                        parsed_data=excluded.parsed_data,
                        status=excluded.status
                ''', (rfq_id, raw_data, parsed_data_str, status))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Error saving RFQ record '{rfq_id}': {e}")
            return False

    def update_rfq_status(self, rfq_id: str, status: str) -> bool:
        """更新詢價歷程狀態 (如 PENDING, SENT, COMPLETED)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE RFQ_History
                    SET status = ?
                    WHERE rfq_id = ?
                ''', (status, rfq_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error updating RFQ status for '{rfq_id}': {e}")
            return False

# 建立預設實例供外部直接匯入使用
db = DBManager()
