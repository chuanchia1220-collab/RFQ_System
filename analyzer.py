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
    
    # 1. 準備純英文的 Enum 清單 (給 Schema 驗證用)
    pure_mat_opts = ", ".join(OPTIONS["material_types"])
    pure_form_opts = ", ".join(OPTIONS["form_types"])

    # 2. 準備中英對照表 (給 AI 理解用，但不作為 Output 標準)
    trans_map = OPTION_TRANSLATIONS.get("zh", {})
    # 讓 AI 知道 316L 是不鏽鋼，但 Output 還是要寫 Stainless Steel
    context_hint = "Reference Map (For understanding only): " + ", ".join([f"{m}={trans_map.get(m, m)}" for m in OPTIONS["material_types"]])

    system_prompt = "You are a senior procurement analyst. Normalize RFQ text into strict JSON validated by schema."

    user_prompt = (
        f"Analyze this RFQ text:\n\"\"\"{text}\"\"\"\n\n"
        f"*** STRICT RULES ***\n"
        f"1. **ROOT OBJECT**: Output MUST be {{ 'items': [...] }}.\n"
        f"2. **MANDATORY FIELDS**: 'material_type', 'material_spec', 'form', 'dimensions', 'quantity', 'notes'.\n"
        f"3. **QUANTITY**: MUST be a string with unit (e.g. '10 pcs'). NEVER output raw numbers (e.g. 2000) or strings without unit.\n"
        f"4. **FORM LOGIC**:\n"
        f"   - **Bar**: 'Ø', 'dia', 'round', or 'D*L'.\n"
        f"   - **Plate**: 'Block', 'Cuboid' or smallest dim >= 10mm.\n"
        f"   - **Sheet**: smallest dim < 10mm.\n"
        f"   - **Tube**: 'Tube', 'Pipe', 'OD/ID'.\n"
        f"5. **VALID VALUES (Strict Enum)**: \n"
        f"   - Material_type MUST be one of: [{pure_mat_opts}]\n"
        f"   - Form MUST be one of: [{pure_form_opts}]\n"
        f"   - {context_hint}\n"
        f"   - If unsure, use 'Other' and explain in notes.\n"
        f"6. **DIMENSIONS**: Keep original string format exactly.\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # 【修正 1】增加重試次數到 5 次
    max_retries = 5
    
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

            # [零成本修復] 自動補全根節點
            if isinstance(raw_data, dict) and "items" not in raw_data:
                if "material_type" in raw_data:
                    raw_data = {"items": [raw_data]}

            # Schema 驗證
            validate(instance=raw_data, schema=RFQ_SCHEMA)
            print("[AI] 驗證通過，資料結構完美。")
            return raw_data

        except ValidationError as ve:
            # 將具體的錯誤回傳給 AI，讓它修正
            error_msg = f"JSON Validation Error: {ve.message}. Please fix the value to match the Schema requirements."
            print(f"[Schema 違規 - 第 {attempt + 1} 次] {ve.message}")
            
            if attempt == max_retries - 1:
                print("[AI] 重試次數耗盡，解析失敗。")
                return {"items": []}
            
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": error_msg})

        except Exception as e:
            print(f"[AI 系統錯誤] {e}")
            return {"items": []}

    return {"items": []}
