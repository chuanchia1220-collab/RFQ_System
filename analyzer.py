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
        f"1. **ROOT OBJECT**: Output MUST be {{ 'items': [...] }}. Do not output a single item object directly.\n"
        f"2. **MANDATORY FIELDS**: 'material_type', 'material_spec', 'form', 'dimensions', 'quantity', 'notes'.\n"
        f"3. **QUANTITY SPLITTING**: One item per quantity tier. Include unit (e.g. '10 pcs').\n"
        f"4. **VALID VALUES**: \n"
        f"   - Materials: {material_opts}\n"
        f"   - Forms: {form_opts}\n"
        f"   - If unsure, use 'Other' and explain in notes.\n"
        f"5. **DIMENSIONS**: Keep original string format exactly.\n"
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

            # --- [零成本修復] 針對您遇到的 'items' 遺失問題 ---
            # 如果 AI 回傳的是單一 Item (字典)，我們幫它包成列表
            if isinstance(raw_data, dict) and "items" not in raw_data:
                # 檢查這是不是一個 Item (有沒有 material_type)
                if "material_type" in raw_data:
                    print("[AI 自動修復] 偵測到根節點遺失，正在補全 'items'...")
                    raw_data = {"items": [raw_data]}

            # --- Schema 驗證 ---
            validate(instance=raw_data, schema=RFQ_SCHEMA)
            print("[AI] 驗證通過，資料結構完美。")
            return raw_data

        except ValidationError as ve:
            error_msg = f"JSON Validation Error: {ve.message}. Fix the JSON structure based on the schema rules."
            print(f"[Schema 違規 - 第 {attempt + 1} 次] {ve.message}")
            
            # 如果是最後一次嘗試，就放棄
            if attempt == max_retries - 1:
                print("[AI] 重試次數耗盡，解析失敗。")
                return {"items": []}
            
            # --- [Retry 邏輯] 將錯誤餵回給 AI ---
            # 1. 把 AI 剛剛講錯的話加進歷史
            messages.append({"role": "assistant", "content": content})
            # 2. 把錯誤訊息加進歷史 (罵它)
            messages.append({"role": "user", "content": error_msg})
            print("[AI] 正在將錯誤訊息回傳給 GPT 進行自我修正...")

        except json.JSONDecodeError:
            print("[AI 錯誤] JSON 格式損壞")
            return {"items": []}
            
        except Exception as e:
            print(f"[AI 系統錯誤] {e}")
            return {"items": []}

    return {"items": []}
