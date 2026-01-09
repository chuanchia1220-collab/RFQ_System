# analyzer.py 完整覆蓋

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

    system_prompt = "你是專業的採購助理，負責將詢價文字轉為精確的 JSON 資料。"
    
    # 強化尺寸與厚度判斷邏輯
    user_prompt = (
        f"請分析以下詢價內容：\n{text}\n\n"
        f"合法材料 (Valid materials): {material_opts}\n"
        f"合法形狀 (Valid forms): {form_opts}\n\n"
        f"*** 執行規範 ***\n"
        f"1. **厚度與形狀規則**：找出尺寸中最小的數值。若最小邊 >= 10mm 或是品項為 'Block' (塊材)，形狀請設為 'Plate' (板材-厚)。\n"
        f"2. **尺寸提取**：請將尺寸完整提取為字串（例如：'30mm*30mm*40mm'），存於 spec.dimensions 欄位中。\n"
        f"3. **數量拆分**：若有多個詢價數量 (如 10pcs, 2000pcs)，請存入 'quantities' 陣列。\n"
        f"4. **材料對照**：'316L' 對應 'Stainless Steel'。\n"
        f"5. **回傳格式**：回傳根節點為 'items' 的 JSON 物件。欄位值必須使用英文代碼。\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        
        # 清理代碼塊
        if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content: content = content.split("```")[1].split("```")[0].strip()

        raw_data = json.loads(content)
        items = raw_data.get("items", [])
        
        final_items = []
        for raw_item in items:
            # 取得 spec 物件，確保 dimensions 存在
            spec = raw_item.get("spec", {})
            
            # 處理數量
            qty = raw_item.get("quantities", [])
            if not qty:
                qty = [spec.get("annual_qty", "-")]

            cleaned = {
                "item_index": raw_item.get("item_index", 0),
                "confidence": raw_item.get("confidence", 0.9),
                "material_type": raw_item.get("material_type", "Other"),
                "form": raw_item.get("form", "Other"),
                "spec": spec,  # 這裡包含 dimensions 字串
                "quantities": qty
            }
            final_items.append(cleaned)

        print(f"[AI] 解析成功，尺寸內容: {[i['spec'].get('dimensions') for i in final_items]}")
        return {"items": final_items}

    except Exception as e:
        print(f"[AI 錯誤] {e}")
        return {"items": []}
