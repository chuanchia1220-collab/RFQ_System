import pandas as pd
import sqlite3
import json

def to_json_list(text):
    if pd.isna(text) or not text: return "[]"
    # 將逗號隔開的文字轉成 JSON 字串格式，符合你的 main.py 邏輯
    items = [i.strip() for i in str(text).split(',')]
    return json.dumps(items)

def import_suppliers(csv_path):
    conn = sqlite3.connect("rfq_system.db")
    df = pd.read_csv(csv_path)
    
    # 格式轉換
    df['materials'] = df['materials'].apply(to_json_list)
    df['forms'] = df['forms'].apply(to_json_list)
    df['qualifications'] = df.get('qualifications', "").apply(to_json_list)

    # 寫入資料庫 (對應 database.py 的欄位)
    df.to_sql('suppliers', conn, if_exists='append', index=False)
    conn.close()
    print("匯入完成！")

if __name__ == "__main__":
    import_suppliers("suppliers_import.csv")
