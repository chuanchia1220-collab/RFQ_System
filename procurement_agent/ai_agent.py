import os
import time
import logging
import json
import sqlite3
import requests
from dotenv import load_dotenv

# Try to import from database.py if available, else hardcode for safety
try:
    from database import DB_NAME
except ImportError:
    DB_NAME = "Supplier_Docs.db"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("system.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY or API_KEY == "your_api_key_here":
    logging.critical("GEMINI_API_KEY not found in environment variables. Terminating.")
    import sys
    sys.exit(1)

def _execute_sql(query: str) -> str:
    """Executes a SQL query against the local SQLite database and returns the result."""
    try:
        # Check if DB is in procurement_agent or current dir
        db_path = DB_NAME
        if not os.path.exists(db_path) and os.path.exists(f"procurement_agent/{DB_NAME}"):
            db_path = f"procurement_agent/{DB_NAME}"

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            return "No results found."

        # Convert rows to a readable list of dicts string
        result = [dict(row) for row in rows]
        return json.dumps(result, ensure_ascii=False, indent=2)
    except sqlite3.Error as e:
        logging.error(f"SQL execution error for query: {query}", exc_info=True)
        return f"Database error: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def _call_gemini_rest_with_retry(prompt: str, retries: int = 3, system_instruction: str = None) -> str:
    """Calls Gemini REST API with strict 3-retry fallback and physical rate-limiting."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Calling Gemini REST API (Attempt {attempt}/{retries})")
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()

            data = response.json()
            if "candidates" in data and data["candidates"]:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            else:
                logging.error(f"Unexpected response format: {data}")
                raise Exception("Unexpected Gemini API response format")

        except requests.exceptions.RequestException as e:
            logging.error(f"Gemini API network error on attempt {attempt}: {e}", exc_info=True)
        except Exception as e:
            logging.error(f"Gemini API general error on attempt {attempt}: {e}", exc_info=True)

        if attempt == retries:
            logging.error("Max retries reached. Returning error message.")
            return "抱歉，系統目前無法連線到 AI 引擎，請稍後再試。"

        # Rate limiting / Backoff
        time.sleep(2 ** attempt)

    return "發生未知錯誤。"

def ask_procurement_agent(user_query: str) -> str:
    """
    Main function for the Chat UI. Converts natural language to SQL,
    executes it, and returns a natural language summary.
    """
    # Step 1: Text-to-SQL
    schema_context = """
    You are an expert SQLite SQL generator. Given a natural language request, generate ONLY the valid SQL query to retrieve the information from the following schema:

    Table: Supplier_Master
    Columns: Supplier_ID (TEXT), Name (TEXT), Email (TEXT), pmn31 (TEXT)

    Table: Document_Master
    Columns: Doc_ID (TEXT), Supplier_ID (TEXT), Doc_Type (TEXT), File_Path (TEXT), Status (TEXT - can be 'signed' or 'pending')

    Rules:
    - Return ONLY the SQL query string. No markdown formatting, no explanations.
    - Missing documents means Status = 'pending'.
    - Signed documents means Status = 'signed'.
    - Use JOIN when necessary.
    """

    sql_prompt = f"User Request: {user_query}\nSQL Query:"

    sql_query = _call_gemini_rest_with_retry(sql_prompt, system_instruction=schema_context).strip()

    # Strip markdown if AI ignored the rule
    if sql_query.startswith("```sql"):
        sql_query = sql_query[6:]
    if sql_query.endswith("```"):
        sql_query = sql_query[:-3]
    sql_query = sql_query.strip()

    logging.info(f"Generated SQL: {sql_query}")

    # Step 2: Execute SQL
    if not sql_query.upper().startswith("SELECT"):
        return "抱歉，我無法將您的請求轉換為安全的查詢語句。"

    db_results = _execute_sql(sql_query)

    # Step 3: Summarize results
    summary_context = "You are a helpful procurement assistant. Summarize the database results to answer the user's question clearly in Traditional Chinese. Keep it professional."
    summary_prompt = f"User Question: {user_query}\n\nDatabase Results:\n{db_results}\n\nPlease provide a clear summary in Traditional Chinese."

    final_answer = _call_gemini_rest_with_retry(summary_prompt, system_instruction=summary_context)

    return final_answer

if __name__ == "__main__":
    # Test execution
    print(ask_procurement_agent("幫我查出目前有哪幾家供應商還沒簽回 NDA？"))