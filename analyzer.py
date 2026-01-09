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

    system_prompt = "你是專業的採購助理。你的任務是將詢價單轉換為結構化 JSON 資料。"
    
    # 【關鍵修正】使用全中文 Prompt，加強厚度判斷邏輯
    user_prompt = (
        f"請分析以下詢價內容 (RFQ text)：\n{text}\n\n"
        f"合法材料 (Valid materials): {material_opts}\n"
        f"合法形狀 (Valid forms): {form_opts}\n\n"
        f"*** 判斷邏輯 (CRITICAL RULES) ***\n"
        f"1. **厚度判斷 (Thickness Logic)**: 找出尺寸中最小的數值視為「厚度」。\n"
        f"   - 若厚度 >= 10mm，形狀設為 'Plate'。\n"
        f"   - 若厚度 < 10mm，形狀設為 'Sheet'。\n"
        f"2. **塊狀規則 (Block Rule)**: 若品項描述為 'Block'、'Cuboid' 或長方體，請歸類為 'Plate'。\n"
        f"3. **材料對照**: '316L' 對應 'Stainless Steel'。\n"
        f"4. **輸出格式**: 僅回傳 JSON 物件，根節點為 'items'。欄位值必須使用上述提供的**英文**選項。\n"
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
            # 確保 AI 判斷的 Form 有被保留
            ai_form = raw_item.get("form", raw_item.get("form_type", "Other"))
            
            cleaned = {
                "item_index": raw_item.get("item_index", 0),
                "confidence": raw_item.get("confidence", 0.9),
                "spec": raw_item.get("spec", raw_item),
                # 這裡會優先抓取 AI 分析出的英文代碼，若無則為 Other
                "material_type": raw_item.get("material_type", raw_item.get("material", "Other")),
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
