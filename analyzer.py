import os
import json
import openai
from pydantic import BaseModel, Field
from typing import List, Literal
from config import OPTIONS

# 1. 定義資料模型 (解決缺口 4, 5: JSON Schema + Sanity Check)
class RFQItem(BaseModel):
    material_type: Literal[
        "Aluminum", "Copper", "Carbon Steel", "Stainless Steel", 
        "Tool Steel", "Nickel Alloy", "Titanium Alloy", "Plastic", "Other"
    ] = Field(description="If unsure, use 'Other'")
    material_spec: str = Field(description="Original material name, e.g., '316L'")
    form: Literal["Bar", "Tube", "Sheet", "Plate", "Forging", "Stamping", "Other"]
    dimensions: str = Field(description="Preserve original textual format exactly.")
    quantity: str = Field(description="Must include numeric value AND unit.")
    notes: str = Field(description="Assumptions, constraints, or fallback reasons.")

class RFQResponse(BaseModel):
    items: List[RFQItem]

def analyze_rfq(text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[錯誤] 找不到 OPENAI_API_KEY")
        return {"items": []}

    client = openai.OpenAI(api_key=api_key)
    
    # 2. 強化 Prompt (解決缺口 1, 2, 3)
    system_prompt = """You are a senior procurement analyst. 
Your task is to normalize RFQ text into a strict structure for supplier quotation emails."""

    user_prompt = f"""Analyze the following RFQ text:
\"\"\"{text}\"\"\"

CRITICAL RULES:
1. FIELD DISCIPLINE: All fields are MANDATORY. Never omit dimensions or quantity.
2. FALLBACK LOGIC: If a value does not match the allowed list, you MUST use "Other" and explain why in 'notes'.
3. DIMENSION PRESERVATION: Dimensions MUST preserve the original textual format (symbols, order). Do NOT normalize or reorder.
4. QUANTITY SPLITTING: Create one item per quantity tier.
5. THICKNESS LOGIC: Minimum dimension >= 10mm or "block/塊材" -> "Plate", else "Sheet".
6. MATERIAL MAPPING: "316L" -> "Stainless Steel"."""

    try:
        # 使用最新 beta.chat.completions.parse 確保 100% 符合 Schema
        completion = client.beta.chat.completions.parse(
            model="gpt-4o",  # 採用 4o 級別模型
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=RFQResponse,
            temperature=0
        )
        
        # 3. 程式碼驗證 (自動執行 Sanity Check)
        result = completion.choices[0].message.parsed
        return result.model_dump()

    except Exception as e:
        print(f"[架構崩潰] AI 輸出不符合合約: {e}")
        return {"items": []}
