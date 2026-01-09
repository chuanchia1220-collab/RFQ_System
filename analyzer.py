import os
import json
import openai
from jsonschema import validate, ValidationError
from config import OPTIONS, OPTION_TRANSLATIONS
from rfq_schema import RFQ_SCHEMA

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

    system_prompt = "You are a senior procurement analyst. Normalize RFQ text into strict JSON validated by schema."

    user_prompt = (
        f"Analyze this RFQ text:\n\"\"\"{text}\"\"\"\n\n"
        f"*** STRICT RULES ***\n"
        f"1. **ROOT OBJECT**: Output MUST be {{ 'items': [...] }}.\n"
        f"2. **MANDATORY FIELDS**: 'material_type', 'material_spec', 'form', 'dimensions', 'quantity', 'notes'.\n"
        f"3. **QUANTITY SPLITTING**: One item per quantity tier.\n"
        f"4. **FORM LOGIC (Priority Order)**:\n"
        f"   - **Bar Rule**: If dimensions contain symbol 'Ø' or words 'dia', 'diameter', 'round', OR format is 'D*L', set form to 'Bar'.\n"
        f"   - **Plate/Block Rule**: If item is 'Block', 'Cuboid' OR smallest dimension >= 10mm, set form to 'Plate'.\n"
        f"   - **Sheet Rule**: If smallest dimension < 10mm, set form to 'Sheet'.\n"
        f"   - **Tube Rule**: If text mentions 'Tube', 'Pipe', 'OD', 'ID', set form to 'Tube'.\n"
        f"5. **DIMENSIONS**: Keep original string format exactly (e.g. 'Ø45*1000mm').\n"
        f"6. **VALID VALUES**: \n"
        f"   - Materials: {material_opts}\n"
        f"   - Forms: {form_opts}\n"
        f"   - If unsure, use 'Other' and explain in notes.\n"
    )

    # 初始化對話歷史
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            print(f"[AI] 第 {attempt + 1} 次嘗試解析...")
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            raw_data = json.loads(content)

            # [零成本修復] 
            if isinstance(raw_data, dict) and "items" not in raw_data:
                if "material_type" in raw_data:
                    raw_data = {"items": [raw_data]}

            # Schema 驗證
            validate(instance=raw_data, schema=RFQ_SCHEMA)
            print("[AI] 驗證通過，資料結構完美。")
            return raw_data

        except ValidationError as ve:
            error_msg = f"JSON Validation Error: {ve.message}. Fix the JSON structure based on the schema rules."
            print(f"[Schema 違規 - 第 {attempt + 1} 次] {ve.message}")
            if attempt == max_retries - 1:
                return {"items": []}
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": error_msg})

        except Exception as e:
            print(f"[AI 系統錯誤] {e}")
            return {"items": []}

    return {"items": []}
