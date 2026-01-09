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
    trans_map = OPTION_TRANSLATIONS.get("zh", {})
    material_opts = ", ".join([f"{m}({trans_map.get(m, m)})" for m in OPTIONS["material_types"]])
    form_opts = ", ".join([f"{f}({trans_map.get(f, f)})" for f in OPTIONS["form_types"]])

    system_prompt = "你是一位精通採購與金屬材料的專家助理。請將詢價內容解析為結構化的 JSON 格式。"
    
    user_prompt = (
        f"請分析以下詢價文字，並拆分為多個品項：\n{text}\n\n"
        f"**規範細則**：\n"
        f"1. **厚度邏輯**：找出尺寸中最小的數值。若最小邊 >= 10mm 或是提及 'Block' (塊材)，形狀請選 'Plate' (板材-厚)。\n"
        f"2. **尺寸提取**：將尺寸存為字串（如：'30mm*30mm*40mm'）放在 spec.dimensions 中。\n"
        f"3. **數量提取**：將數量存為陣列存於 quantities 欄位。\n"
        f"4. **材料匹配**：'316L' 必須對應到 'Stainless Steel'。\n"
        f"**選項限制**（必須使用英文代碼）：\n"
        f"- 材料種類: {material_opts}\n"
        f"- 形狀: {form_opts}\n\n"
        f"請務必回傳根鍵值為 'items' 的 JSON 物件。"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content: content = content.split("```")[1].split("```")[0].strip()

        raw_data = json.loads(content)
        items = raw_data.get("items", [])
        
        final_items = []
        for raw_item in items:
            # 容錯處理：檢查多種可能的欄位名稱
            mat = raw_item.get("material_type") or raw_item.get("material") or "Other"
            frm = raw_item.get("form") or raw_item.get("form_type") or "Other"
            spec = raw_item.get("spec", {})
            
            final_items.append({
                "item_index": raw_item.get("item_index", 0),
                "confidence": raw_item.get("confidence", 0.9),
                "material_type": mat,
                "form": frm,
                "spec": spec,
                "quantities": raw_item.get("quantities") or [spec.get("annual_qty", "-")]
            })

        print(f"[AI] 解析成功，品項: {[i['material_type'] + '-' + i['form'] for i in final_items]}")
        return {"items": final_items}
    except Exception as e:
        print(f"[AI 錯誤] {e}")
        return {"items": []}
