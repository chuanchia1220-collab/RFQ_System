# **RFQ-SPEC v1.0**

時碩 RFQ 自動化系統 — 規格說明書（工程師版）

版本：v1.0  
狀態：凍結（後續變更請以 v1.1 / v1.2 方式增量修改）

* * *

## **1. 系統目標與範圍**

### **1.1 系統目標**

本系統旨在協助採購人員，將工程師提供的原始詢價文字（Email / 文字描述）：

1.  自動解析為一筆或多筆材料項目（RFQ Items）
    
2.  依材料種類、形狀、認證等級，自動匹配供應商
    
3.  依模板產生標準化 RFQ Email 內容
    
4.  透過 Outlook COM 在本機建立草稿信件，供人工確認後送出
    

### **1.2 系統範圍（v1.0）**

*   供應商資料管理（CRUD）
    
*   RFQ 文字解析（GPT-based）
    
*   多材料項目拆分
    
*   供應商自動匹配
    
*   Email 模板管理
    
*   RFQ 歷史紀錄查詢
    
*   Outlook COM 草稿建立
    

* * *

## **2. 資料設計原則**

1.  **資料庫一律存英文代碼**
    
    *   金屬種類 / 形狀 / 認證等級皆使用固定英文值
        
    *   UI 顯示文字由前端對照表控制，可隨時調整，不影響 DB
        
2.  **國家欄位（country）**
    
    *   DB 使用自由文字
        
    *   UI 可提供下拉或自動完成，但不限制輸入
        
3.  **結構化優先**
    
    *   關鍵欄位結構化
        
    *   不確定或彈性內容以 JSON 儲存
        

* * *

## **3. 固定選項（DB Enum 值）**

### **3.1 金屬種類（material_type）**

*   Aluminum
    
*   Copper
    
*   Carbon Steel
    
*   Stainless Steel
    
*   Tool Steel
    
*   Nickel Alloy
    
*   Titanium Alloy
    
*   Plastic
    
*   Other
    

### **3.2 形狀（form_type）**

*   Bar
    
*   Tube
    
*   Sheet
    
*   Plate
    
*   Forging
    
*   Stamping
    
*   Other
    

### **3.3 認證等級（qualification）**

*   ISO
    
*   Automotive
    
*   Aerospace
    

* * *

## **4. 資料庫 Schema（PostgreSQL）**

### **4.1 suppliers**

CREATE TABLE suppliers (  
id SERIAL PRIMARY KEY,  
name TEXT NOT NULL,  
emails TEXT,  
country TEXT,  
materials TEXT[],  
forms TEXT[],  
qualifications TEXT[],  
capabilities TEXT,  
notes TEXT,  
enabled BOOLEAN DEFAULT TRUE,  
created_at TIMESTAMP DEFAULT now(),  
updated_at TIMESTAMP DEFAULT now()  
);

### **4.2 templates**

CREATE TABLE templates (  
id SERIAL PRIMARY KEY,  
name TEXT NOT NULL,  
subject_format TEXT,  
preamble_html TEXT,  
closing_html TEXT,  
table_fields JSONB,  
font_family TEXT,  
font_size INT,  
table_styles JSONB,  
created_by TEXT,  
created_at TIMESTAMP DEFAULT now()  
);

### **4.3 rfq_requests**

CREATE TABLE rfq_requests (  
id SERIAL PRIMARY KEY,  
raw_text TEXT,  
parsed_items JSONB,  
created_by TEXT,  
status TEXT,  
created_at TIMESTAMP DEFAULT now()  
);

### **4.4 rfq_items**

CREATE TABLE rfq_items (  
id SERIAL PRIMARY KEY,  
request_id INT REFERENCES rfq_requests(id),  
item_index INT,  
material_type TEXT,  
form_type TEXT,  
spec JSONB,  
matched_suppliers INT[],  
selected_supplier INT,  
email_payload JSONB,  
status TEXT,  
created_at TIMESTAMP DEFAULT now()  
);

* * *

## **5. 供應商匹配邏輯（Supplier Matching Engine）**

### **5.1 匹配條件與順序**

1.  材料種類（material_type）必須符合
    
2.  形狀（form_type）至少一項符合
    
3.  若需求中明確提到認證等級，供應商必須符合
    
4.  國家不做強制篩選，僅作顯示用途
    

### **5.2 匹配結果處理**

*   若找不到符合供應商：
    
    *   rfq_items.status = `no_supplier_found`
        
    *   UI 顯示需人工處理提示
        

* * *

## **6. GPT 解析輸出格式（強制）**

{  
"items": [  
{  
"item_index": 0,  
"material_type": "Stainless Steel",  
"form": "Bar",  
"spec": {  
"description": "",  
"dimensions": {  
"d": "",  
"L": "",  
"thickness": "",  
"width": ""  
},  
"tolerance": "",  
"annual_qty": "",  
"unit": "pcs/kg/m",  
"need_by": "",  
"surface_finish": "",  
"heat_treatment": ""  
},  
"notes": "",  
"confidence": 0.0  
}  
]  
}

### **6.1 GPT 約束條件**

*   僅輸出有效 JSON
    
*   material_type / form 必須使用固定英文值
    
*   無法判斷欄位填空字串或 null
    
*   confidence 低於門檻（建議 0.6）需人工確認
    

* * *

## **7. Email 與 Outlook 規範**

### **7.1 Email Subject 規則**

時碩詢價單 {yymmddHH}_{supplier_name}

範例：

時碩詢價單 25120914_鼎新鋼業股份有限公司

### **7.2 Outlook COM 建立草稿**

*   使用 Outlook COM Automation
    
*   建立 MailItem 並儲存為 Draft
    
*   禁止系統自動送出 Email
    

* * *

## **8. UI 設計約束（摘要）**

*   金屬種類 / 形狀 / 認證等級：
    
    *   僅能選擇固定選項
        
    *   不允許自由輸入
        
*   UI 顯示文字與 DB 英文代碼解耦
    
*   低 confidence 項目需顯示警示
    

* * *

## **9. 安全與稽核**

*   API 採用 JWT 驗證
    
*   重要操作需記錄 log（request_id / user / timestamp）
    
*   Outlook Agent 回報草稿建立結果供稽核
    

* * *

## **10. 版本管理**

*   本文件為 RFQ-SPEC v1.0（凍結）
    
*   後續修改請建立 v1.1 / v1.2 文件
    
*   不直接覆寫 v1.0
