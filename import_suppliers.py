import sqlite3
import csv
import json
import os

# 設定資料庫檔案名稱 (需與 database.py 一致)
DB_NAME = "rfq_system.db"

def clean_and_json(value_str):
    """將逗號分隔的字串轉換為 JSON 陣列"""
    if not value_str or value_str.strip() == "":
        return json.dumps([])
    # 拆分、去除空白並過濾掉空值
    items = [item.strip() for item in value_str.split(",") if item.strip()]
    return json.dumps(items)

def import_from_csv(csv_file):
    if not os.path.exists(csv_file):
        print(f"錯誤：找不到檔案 {csv_file}")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    count = 0
    try:
        with open(csv_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 轉換多選欄位為 JSON 格式
                materials_json = clean_and_json(row['Materials'])
                forms_json = clean_and_json(row['Forms'])
                quals_json = clean_and_json(row['Qualifications'])

                cursor.execute('''
                    INSERT INTO suppliers (
                        name, contact_person, email, phone, address, 
                        materials, forms, qualifications
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['Name'],
                    row['Contact'],
                    row['Email'],
                    row['Phone'],
                    row['Address'],
                    materials_json,
                    forms_json,
                    quals_json
                ))
                count += 1
        
        conn.commit()
        print(f"成功！已匯入 {count} 筆供應商資料。")

    except Exception as e:
        print(f"匯入失敗：{e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # 請確保您的 CSV 檔名為 suppliers.csv
    import_from_csv("suppliers.csv")
