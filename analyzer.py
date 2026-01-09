import os
import json
import openai
from config import OPTIONS, OPTION_TRANSLATIONS

def analyze_rfq(text):
    print(f"\n[AI] 收到解析請求，長度: {len(text)}")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[AI 錯誤] 找不到 OPENAI_API_KEY")
        return {"items": []}

    client = openai.OpenAI(api_key=api_key)

    # 動態生成中英對照
    trans_map = OPTION_TRANSLATIONS.get("zh", {})
    material_opts_list = [f"{m} ({trans_map.get(m, m)})" for m in OPTIONS["material_types"]]
    form_opts_list = [f"{f} ({trans_map.get(f, f)})" for f in OPTIONS["form_types"]]
    
    material_opts = ", ".join(material_opts_list)
    form_opts = ", ".join(form_opts_list)

    system_prompt = "你是專業的採購助理。你的任務是將詢價單轉換為結構化 JSON 資料。"
    
    # 【關鍵修正】加入多數量 (quantities) 的提取邏輯
    user_prompt = (
        f"請分析以下詢價內容 (RFQ text)：\n{text}\n\n"
        f"合法材料選項 (Valid materials): {material_opts}\n"
        f"合法形狀選項 (Valid forms): {form_opts}\n\n"
        f"*** 判斷邏輯 (CRITICAL RULES) ***\n"
        f"1. **厚度判斷**: 找出尺寸中最小的數值視為「厚度」。\n"
        f"   - 若厚度 >= 10mm，形狀設為 'Plate'。\n"
        f"   - 若厚度 < 10mm，形狀設為 'Sheet'。\n"
        f"2. **塊狀規則**: 若品項描述為 'Block'、'Cuboid'，請歸類為 'Plate'。\n"
        f"3. **材料對照**: '316L' 屬於 'Stainless Steel'。\n"
        f"4. **數量邏輯 (Quantity)**: 若同一品項有多個詢價數量 (例如 10pcs 和 2000pcs)，請提取為陣列。\n"
        f"   - 欄位名稱必須為 'quantities' (Array of integers/strings)。\n"
        f"5. **輸出格式**: \n"
        f"   - 僅回傳 JSON 物件，根節點為 'items'。\n"
        f"   - 每個 item 需包含 'quantities' 欄位。\n"
        f"   - 欄位值必須只回傳「英文代碼」。\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        
        print(f"[AI Debug] 原始回傳內容: >>>{content}<<<")

        if not content:
            print("[AI 錯誤] AI 回傳空字串")
            return {"items": []}

        if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content: content = content.split("```")[1].split("```")[0].strip()

        raw_data = json.loads(content)
        
        items = []
        for key in ["items", "RFQ_items", "rfq_items", "Items"]:
            if key in raw_data:
                items = raw_data[key]
                break
        
        final_items = []
        for raw_item in items:
            ai_form = raw_item.get("form", raw_item.get("form_type", "Other"))
            
            # 確保 quantities 是個列表
            qty = raw_item.get("quantities", raw_item.get("quantity", []))
            if not isinstance(qty, list):
                qty = [qty] if qty else []

            cleaned = {
                "item_index": raw_item.get("item_index", 0),
                "confidence": raw_item.get("confidence", 0.9),
                "spec": raw_item.get("spec", raw_item),
                "material_type": raw_item.get("material_type", raw_item.get("material", "Other")),
                "form": ai_form,
                "quantities": qty # 這裡會儲存 [10, 2000]
            }
            final_items.append(cleaned)

        print(f"[AI] 解析成功，取得 {len(final_items)} 筆資料")
        return {"items": final_items}

    except json.JSONDecodeError as e:
        print(f"[AI 錯誤] JSON 解析失敗: {e}")
        return {"items": []}
    except Exception as e:
        print(f"[AI 錯誤] {e}")
        return {"items": []}
