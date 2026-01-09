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
    
    # 這裡強化對 "items" 這個標籤的命令
    user_prompt = (
        f"Analyze this text:\n{text}\n\n"
        f"Valid materials: {material_opts}\n"
        f"Valid forms: {form_opts}\n"
        f"IMPORTANT: You must use 'items' as the root key in your JSON response."
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

        raw_result = json.loads(content)
        
        # --- 自動修正鍵值邏輯 ---
        final_items = []
        # 如果 AI 寫錯標籤 (例如寫成 RFQ_items)，自動把它轉過來
        for key in ["items", "RFQ_items", "rfq_items", "Items"]:
            if key in raw_result:
                final_items = raw_result[key]
                break
        
        print(f"[AI 階段 4] 修正後取得 {len(final_items)} 個項目")
        return {"items": final_items}

    except Exception as e:
        print(f"[AI 錯誤] {e}")
        return {"items": []}
