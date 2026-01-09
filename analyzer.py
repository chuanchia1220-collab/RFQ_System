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

    system_prompt = "You are an expert procurement assistant."
    
    # 【關鍵修正】: 加入板材厚度判斷與 Block 歸類邏輯
    user_prompt = (
        f"Analyze this RFQ text:\n{text}\n\n"
        f"Valid materials: {material_opts}\n"
        f"Valid forms: {form_opts}\n\n"
        f"Logic Rules:\n"
        f"1. **Block/Plate Rule**: If the item is described as 'Block', classify as 'Plate'.\n"
        f"2. **Thickness Rule**: For flat items (Plate/Sheet/Strip/Block) or items with 3 dimensions:\n"
        f"   - Identifty the smallest dimension as 'Thickness'.\n"
        f"   - If Thickness < 10mm, classify as 'Sheet'.\n"
        f"   - If Thickness >= 10mm, classify as 'Plate'.\n"
        f"3. **Bar Rule**: Only classify as 'Bar' if it is explicitly 'Bar', 'Rod', or long/cylindrical items not matching the Plate rule.\n"
        f"4. Return ONLY a JSON object with a root key 'items'.\n"
        f"5. Each item must have 'material_type' and 'form' strictly from the valid lists."
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
        
        items = []
        for key in ["items", "RFQ_items", "rfq_items", "Items"]:
            if key in raw_data:
                items = raw_data[key]
                break
        
        final_items = []
        for raw_item in items:
            cleaned = {
                "item_index": raw_item.get("item_index", 0),
                "confidence": raw_item.get("confidence", 0.9),
                "spec": raw_item.get("spec", raw_item),
                "material_type": raw_item.get("material_type", raw_item.get("material", "Other")),
                "form": raw_item.get("form", raw_item.get("form_type", "Other")) 
            }
            final_items.append(cleaned)

        print(f"[AI 階段 4] 智慧判斷完成 (含厚度邏輯)，取得 {len(final_items)} 個項目")
        return {"items": final_items}

    except Exception as e:
        print(f"[AI 錯誤] {e}")
        return {"items": []}
