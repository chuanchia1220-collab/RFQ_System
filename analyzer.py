import os
import json
import openai
from jsonschema import validate, ValidationError
from config import OPTIONS, OPTION_TRANSLATIONS
from rfq_schema import RFQ_SCHEMA  # 匯入憲法

def analyze_rfq(text):
    print(f"\n[AI] 收到解析請求，長度: {len(text)}")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[AI 錯誤] 找不到 OPENAI_API_KEY")
        return {"items": []}

    client = openai.OpenAI(api_key=api_key)
    
    # 動態生成 Prompt 的輔助資訊
    trans_map = OPTION_TRANSLATIONS.get("zh", {})
    material_opts = ", ".join([f"{m}({trans_map.get(m, m)})" for m in OPTIONS["material_types"]])
    form_opts = ", ".join([f"{f}({trans_map.get(f, f)})" for f in OPTIONS["form_types"]])

    system_prompt = "You are a senior procurement analyst. Your task is to normalize RFQ text into a strict JSON structure validated by a schema."

    user_prompt = (
        f"Analyze the following RFQ text:\n\"\"\"{text}\"\"\"\n\n"
        f"*** STRICT RULES (Follow these or validation will fail) ***\n"
        f"1. **MANDATORY FIELDS**: 'material_type', 'material_spec', 'form', 'dimensions', 'quantity', 'notes'. NEVER omit any.\n"
        f"2. **QUANTITY SPLITTING**: One item per quantity tier. Quantity MUST include unit (e.g., '10 pcs', not just '10').\n"
        f"3. **THICKNESS LOGIC**: If smallest dimension >= 10mm or text mentions 'block', use 'Plate'. Else 'Sheet'.\n"
        f"4. **DIMENSION PRESERVATION**: Keep original string format exactly (e.g., '30mm*30mm*40mm').\n"
        f"5. **VALID VALUES ONLY**: \n"
        f"   - Materials: {material_opts}\n"
        f"   - Forms: {form_opts}\n"
        f"   - If unsure, map to 'Other' and explain in notes.\n"
        f"6. **MATERIAL MAPPING**: '316L' -> 'Stainless Steel'.\n\n"
        f"Return ONLY a valid JSON object matching the schema."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        raw_data = json.loads(content)

        # 🔒 關鍵步驟：Schema 執法
        print("[AI] 正在進行 Schema 結構驗證...")
        validate(instance=raw_data, schema=RFQ_SCHEMA)
        print("[AI] 驗證通過，資料結構完美。")

        return raw_data

    except ValidationError as ve:
        # 這裡會抓到 AI 偷懶的證據 (例如 quantity 沒單位，或 form 亂寫)
        print(f"[Schema 違規] AI 輸出不符合契約: {ve.message}")
        print(f"[違規資料片段] {ve.instance}")
        # 實務上這裡可以做 retry，但在 v1.0我們先回傳空陣列避免報錯
        return {"items": []}

    except json.JSONDecodeError:
        print("[AI 錯誤] JSON 格式損壞")
        return {"items": []}
        
    except Exception as e:
        print(f"[AI 系統錯誤] {e}")
        return {"items": []}
