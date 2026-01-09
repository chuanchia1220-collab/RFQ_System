import os
import json
import openai
from config import OPTIONS

def analyze_rfq(text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not found.")
        return {"items": []}

    client = openai.OpenAI(api_key=api_key)
    material_opts = ", ".join(OPTIONS["material_types"])
    form_opts = ", ".join(OPTIONS["form_types"])

    system_prompt = "You are an expert procurement assistant. Extract RFQ items into structured JSON."
    json_structure_example = '{"items": [{"item_index": 0, "material_type": "Stainless Steel", "form": "Bar", "spec": {"annual_qty": "", "unit": "pcs", "dimensions": {}}, "confidence": 0.95}]}'

    user_prompt = (
        f"Analyze this text:\n{text}\n\n"
        f"Valid materials: {material_opts}\nValid forms: {form_opts}\n"
        f"Return ONLY JSON strictly following this structure: {json_structure_example}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        
        # 清理 GPT 可能加入的 Markdown 標籤
        if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content: content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        # 確保 'items' 鍵值存在，以符合 main.py 的需求
        if "items" not in result:
            result["items"] = []

        return result # 確保這裡回傳的是包含 items 的完整字典
    except Exception as e:
        print(f"Error analyzing RFQ: {e}")
        return {"items": []}
