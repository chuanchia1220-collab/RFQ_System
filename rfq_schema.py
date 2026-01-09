# rfq_schema.py
# 這是系統的「憲法」，定義了 AI 輸出的絕對邊界

RFQ_SCHEMA = {
  "type": "object",
  "required": ["items"],
  "properties": {
    "items": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": [
          "material_type",
          "material_spec",
          "form",
          "dimensions",
          "quantity",
          "qualification",
          "notes"
        ],
        "properties": {
          "material_type": {
            "type": "string",
            "description": "Must match the system's material list exactly.",
            "enum": [
              "Aluminum",
              "Copper",
              "Carbon Steel",
              "Stainless Steel",
              "Tool Steel",
              "Nickel Alloy",
              "Titanium Alloy",
              "Plastic",
              "Other"
            ]
          },
          "material_spec": {
            "type": "string",
            "minLength": 1,
            "description": "The raw material specification string, e.g. '316L'."
          },
          "form": {
            "type": "string",
            "enum": [
              "Bar",
              "Tube",
              "Sheet",
              "Plate",
              "Forging",
              "Stamping",
              "Other"
            ]
          },
          "dimensions": {
            "type": "string",
            "minLength": 1,
            "description": "Original dimension string, preserving symbols and order."
          },
          "quantity": {
            "type": "string",
            "description": "Number followed by unit. e.g. '10 pcs'.",
            # Regex 解釋：
            # ^[0-9.,]+ : 開頭必須是數字、點或逗號
            # \s* : 允許中間有空白
            # [a-zA-Z]+$: 結尾必須是英文單位
            "pattern": "^[0-9.,]+\\s*[a-zA-Z]+$"
          },
          "qualification": { "type": "string", "enum": ["ISO", "Automotive", "Aerospace"] },
          "notes": {
            "type": "string",
            "description": "Inference logic, assumptions, or raw constraints."
          }
        },
        "additionalProperties": False
      }
    }
  },
  "additionalProperties": False
}
