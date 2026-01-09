import os
import json
import openai
from config import OPTIONS

def analyze_rfq(text):
    print(f"\n[AI] 收到解析請求，長度: {len(text)}")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[AI 錯誤] 找不到 OPENAI_API_KEY")
        return {"items": []}

    client = openai.OpenAI(api_key=api_key)
    material_opts = ", ".join(OPTIONS["material_types"])
    form_opts = ", ".join(OPTIONS["form_types"])

    system_prompt = "You are an expert procurement assistant. You MUST return valid JSON."
    
    # 【關鍵修正】寫入你的 10mm 黃金法則 + Block 歸類
    user_prompt = (
        f"Analyze this RFQ text:\n{text}\n\n"
        f"Valid materials: {material_opts}\n"
        f"Valid forms: {form_opts}\n\n"
        f"*** CRITICAL RULES ***\n"
        f"1. **Thickness Logic**: Identify dimensions. Find the SMALLEST dimension as 'Thickness'.\n"
        f"   - If Thickness >= 10mm, set form to 'Plate'.\n"
        f"   - If Thickness < 10mm, set form to 'Sheet'.\n"
        f"2. **Block Rule**: If item is 'Block' or 'Cuboid' (3D), treat it as 'Plate'.\n"
        f"3. **Material**: '316L' is 'Stainless Steel'.\n"
        f"4. **Format**: Return ONLY a JSON object with a root key 'items'. NO markdown, NO comments.\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        
        # 【除錯關鍵】印出 AI 到底回傳了什麼
        print(f"[AI Debug] 原始回傳內容: >>>{content}<<<")

        if not content:
            print("[AI 錯誤] AI 回傳了空字串，可能是 API 額度不足或被限制。")
            return {"items": []}

        # 清理 Markdown
        if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content: content = content.split("```")[1].split("```")[0].strip()

        raw_data = json.loads(content)
        
        # 容錯抓取 items
        items = []
        for key in ["items", "RFQ_items", "rfq_items", "Items"]:
            if key in raw_data:
                items = raw_data[key]
                break
        
        final_items = []
        for raw_item in items:
            # 確保 AI 判斷的 Form 有被保留 (這裡會是 Plate 或 Sheet)
            ai_form = raw_item.get("form", raw_item.get("form_type", "Other"))
            
            cleaned = {
                "item_index": raw_item.get("item_index", 0),
                "confidence": raw_item.get("confidence", 0.9),
                "spec": raw_item.get("spec", raw_item),
                "material_type": raw_item.get("material_type", "Other"),
                "form": ai_form 
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
