import os
import json
import openai
from config import OPTIONS

def analyze_rfq(text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[錯誤] 找不到 OPENAI_API_KEY")
        return {"items": []}

    client = openai.OpenAI(api_key=api_key)
    material_opts = ", ".join(OPTIONS["material_types"])
    form_opts = ", ".join(OPTIONS["form_types"])

    system_prompt = "You are an expert procurement assistant. Extract RFQ items into structured JSON."
    
    # 強制 AI 使用特定結構，並提供範例
    user_prompt = (
        f"Analyze this text:\n{text}\n\n"
        f"Valid materials: {material_opts}\n"
        f"Valid forms: {form_opts}\n"
        f"Return ONLY a JSON object with a root key 'items'. Each item must have 'material_type' and 'form'."
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
        
        # 1. 自動校正根節點名稱
        items = []
        for key in ["items", "RFQ_items", "rfq_items", "Items"]:
            if key in raw_data:
                items = raw_data[key]
                break
        
        # 2. 自動校正內部欄位名稱 (對齊 main.py 的需求)
        final_items = []
        for raw_item in items:
            cleaned = {
                "item_index": raw_item.get("item_index", 0),
                "confidence": raw_item.get("confidence", 0.9),
                "spec": raw_item.get("spec", raw_item), # 容錯處理：如果沒有 spec 層級就用原始層級
                # 關鍵修正：確保 material_type 和 form 存在
                "material_type": raw_item.get("material_type", raw_item.get("material", "Other")),
                "form": raw_item.get("form", raw_item.get("form_type", raw_item.get("size", "Other")))
            }
            final_items.append(cleaned)

        print(f"[AI 階段 4] 格式校正完成，取得 {len(final_items)} 個項目")
        return {"items": final_items}

    except Exception as e:
        print(f"[AI 錯誤] {e}")
        return {"items": []}
