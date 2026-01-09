import os
import json
import openai
from config import OPTIONS

def analyze_rfq(text):
    print("\n[AI 階段 1] 開始解析流程...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[錯誤] 找不到環境變數 OPENAI_API_KEY")
        return {"items": []}

    client = openai.OpenAI(api_key=api_key)
    material_opts = ", ".join(OPTIONS["material_types"])
    form_opts = ", ".join(OPTIONS["form_types"])

    system_prompt = "You are an expert procurement assistant. Extract RFQ items into structured JSON."
    json_structure_example = '{"items": [{"item_index": 0, "material_type": "Stainless Steel", "form": "Bar", "spec": {"annual_qty": ""}, "confidence": 0.95}]}'

    user_prompt = f"Analyze this text:\n{text}\n\nValid materials: {material_opts}\nValid forms: {form_opts}\nReturn ONLY JSON: {json_structure_example}"

    try:
        print("[AI 階段 2] 正在呼叫 OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        print(f"[AI 階段 3] AI 回傳原始內容: {content}")

        if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content: content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)
        print(f"[AI 階段 4] JSON 解析成功，取得 {len(result.get('items', []))} 個項目")
        return result if "items" in result else {"items": []}
    except Exception as e:
        print(f"[AI 錯誤] 詳細原因: {e}")
        return {"items": []}
